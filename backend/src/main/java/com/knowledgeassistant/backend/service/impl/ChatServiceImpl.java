package com.knowledgeassistant.backend.service.impl;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.knowledgeassistant.backend.dto.chat.ChatSessionResponse;
import com.knowledgeassistant.backend.dto.chat.CreateSessionRequest;
import com.knowledgeassistant.backend.dto.chat.QaPairResponse;
import com.knowledgeassistant.backend.entity.ChatSession;
import com.knowledgeassistant.backend.entity.QaPair;
import com.knowledgeassistant.backend.entity.User;
import com.knowledgeassistant.backend.repository.ChatSessionRepository;
import com.knowledgeassistant.backend.repository.QaPairRepository;
import com.knowledgeassistant.backend.repository.UserRepository;
import com.knowledgeassistant.backend.service.ChatService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentLinkedQueue;
import java.util.stream.Collectors;

/** Implementation of ChatService to manage sessions and orchestrate streaming RAG queries. */
@Service
public class ChatServiceImpl implements ChatService {

    private static final Logger log = LoggerFactory.getLogger(ChatServiceImpl.class);

    private final ChatSessionRepository chatSessionRepository;
    private final QaPairRepository qaPairRepository;
    private final UserRepository userRepository;
    private final ObjectMapper objectMapper;
    private final HttpClient httpClient;

    private final String ragServiceUrl;
    private final String internalApiKey;
    private final int rateLimitRequestsPerMinute;

    // Hand-rolled sliding window rate limiter state
    private final ConcurrentHashMap<UUID, ConcurrentLinkedQueue<Long>> requestTimestamps = new ConcurrentHashMap<>();

    public ChatServiceImpl(
            ChatSessionRepository chatSessionRepository,
            QaPairRepository qaPairRepository,
            UserRepository userRepository,
            ObjectMapper objectMapper,
            @Value("${app.rag-service-url:http://rag-service:8000}") String ragServiceUrl,
            @Value("${app.internal-api-key:default-dev-key}") String internalApiKey,
            @Value("${app.rate-limit.requests-per-minute:10}") int rateLimitRequestsPerMinute) {
        this.chatSessionRepository = chatSessionRepository;
        this.qaPairRepository = qaPairRepository;
        this.userRepository = userRepository;
        this.objectMapper = objectMapper;
        this.ragServiceUrl = ragServiceUrl;
        this.internalApiKey = internalApiKey;
        this.rateLimitRequestsPerMinute = rateLimitRequestsPerMinute;
        this.httpClient = HttpClient.newBuilder().build();
    }

    @Override
    public ChatSessionResponse createSession(CreateSessionRequest request, UUID userId) {
        User user = userRepository.getReferenceById(userId);
        
        String title = (request != null && request.title() != null && !request.title().isBlank())
                ? request.title()
                : "New Chat " + Instant.now().toString();

        ChatSession session = ChatSession.builder()
                .owner(user)
                .title(title)
                .build();

        session = chatSessionRepository.save(session);
        return new ChatSessionResponse(session.getId(), session.getTitle(), session.getCreatedAt());
    }

    @Override
    public List<ChatSessionResponse> getUserSessions(UUID userId) {
        return chatSessionRepository.findByOwnerIdOrderByCreatedAtDesc(userId)
                .stream()
                .map(s -> new ChatSessionResponse(s.getId(), s.getTitle(), s.getCreatedAt()))
                .collect(Collectors.toList());
    }

    @Override
    public List<QaPairResponse> getSessionMessages(UUID sessionId, UUID userId) {
        // Ensure session exists and is owned by the user (USP #5)
        chatSessionRepository.findByIdAndOwnerId(sessionId, userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Chat session not found"));

        return qaPairRepository.findByChatSessionIdOrderByCreatedAtAsc(sessionId)
                .stream()
                .map(this::mapToQaPairResponse)
                .collect(Collectors.toList());
    }

    @Override
    public SseEmitter askQuestionStream(UUID sessionId, UUID userId, String question) {
        // 1. Session ownership validation
        ChatSession session = chatSessionRepository.findByIdAndOwnerId(sessionId, userId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Chat session not found"));

        // 2. Sliding window rate limit check
        enforceRateLimit(userId);

        // 3. Setup SSE emitter (long timeout to prevent client drops during thinking)
        SseEmitter emitter = new SseEmitter(180000L); // 3 minutes
        
        // Setup payload for rag-service
        String requestBody;
        try {
            requestBody = objectMapper.writeValueAsString(new RagQueryRequest(userId.toString(), question));
        } catch (JsonProcessingException e) {
            log.error("Failed to serialize RAG query request", e);
            throw new RuntimeException("Failed to serialize RAG request", e);
        }

        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create(ragServiceUrl + "/internal/query-stream"))
                .header("Content-Type", "application/json")
                .header("X-Internal-Api-Key", internalApiKey)
                .timeout(Duration.ofSeconds(120)) // Generous timeout for slow inference
                .POST(HttpRequest.BodyPublishers.ofString(requestBody))
                .build();

        // Run on a separate thread so we don't block a Tomcat NIO thread.
        // Use synchronous httpClient.send (NOT sendAsync) so this thread
        // stays alive for the entire duration of the streaming response.
        CompletableFuture.runAsync(() -> {
            StringBuilder fullAnswer = new StringBuilder();
            StringBuilder sourcesJson = new StringBuilder();
            
            try {
                HttpResponse<java.util.stream.Stream<String>> response =
                        httpClient.send(request, HttpResponse.BodyHandlers.ofLines());

                if (response.statusCode() != 200) {
                    log.error("rag-service returned HTTP {}", response.statusCode());
                    sendErrorEvent(emitter, "RAG service returned HTTP " + response.statusCode());
                    emitter.completeWithError(new RuntimeException("Downstream HTTP error"));
                    return;
                }

                // Process streaming lines — this blocks until the rag-service
                // stream closes, which is exactly what we want.
                response.body().forEach(line -> {
                    if (line == null || line.isBlank()) return;
                    try {
                        JsonNode node = objectMapper.readTree(line);
                        String type = node.path("type").asText();
                        
                        if ("sources".equals(type)) {
                            JsonNode sourcesNode = node.path("sources");
                            sourcesJson.append(sourcesNode.toString());
                            emitter.send(SseEmitter.event().name("sources").data(line));
                        } else if ("token".equals(type)) {
                            String text = node.path("text").asText();
                            fullAnswer.append(text);
                            emitter.send(SseEmitter.event().name("token").data(line));
                        } else if ("done".equals(type)) {
                            // Save history before completing
                            saveQaPair(session, question, fullAnswer.toString(), sourcesJson.toString());
                            emitter.send(SseEmitter.event().name("done").data(line));
                            emitter.complete();
                        } else if ("error".equals(type)) {
                            String msg = node.path("message").asText();
                            sendErrorEvent(emitter, msg);
                            emitter.completeWithError(new RuntimeException("LLM Error: " + msg));
                        }
                    } catch (Exception e) {
                        log.error("Error processing stream line", e);
                    }
                });
            } catch (Exception ex) {
                log.error("HTTP request to rag-service failed", ex);
                sendErrorEvent(emitter, "Failed to communicate with RAG service: " + ex.getMessage());
                emitter.completeWithError(ex);
            }
        });

        return emitter;
    }

    private void enforceRateLimit(UUID userId) {
        long now = System.currentTimeMillis();
        long oneMinuteAgo = now - 60000;
        
        ConcurrentLinkedQueue<Long> timestamps = requestTimestamps.computeIfAbsent(userId, k -> new ConcurrentLinkedQueue<>());
        
        // Clean old requests
        while (!timestamps.isEmpty() && timestamps.peek() < oneMinuteAgo) {
            timestamps.poll();
        }
        
        if (timestamps.size() >= rateLimitRequestsPerMinute) {
            log.warn("Rate limit exceeded for user {}", userId);
            throw new ResponseStatusException(HttpStatus.TOO_MANY_REQUESTS, "Rate limit exceeded. Try again later.");
        }
        
        timestamps.offer(now);
    }
    
    private void sendErrorEvent(SseEmitter emitter, String message) {
        try {
            String errorJson = objectMapper.writeValueAsString(new ErrorEvent("error", message));
            emitter.send(SseEmitter.event().name("error").data(errorJson));
        } catch (Exception ignored) {
            // Nothing we can do if we can't even send the error event
        }
    }

    private void saveQaPair(ChatSession session, String question, String answer, String sourcesJson) {
        try {
            // Default to empty array if no sources were recorded
            if (sourcesJson == null || sourcesJson.isBlank()) {
                sourcesJson = "[]";
            }
            QaPair pair = QaPair.builder()
                    .chatSession(session)
                    .question(question)
                    .answer(answer)
                    .contextChunks(sourcesJson)
                    .build();
            qaPairRepository.save(pair);
        } catch (Exception e) {
            log.error("Failed to save QA pair to history", e);
        }
    }

    private QaPairResponse mapToQaPairResponse(QaPair pair) {
        JsonNode sourcesNode = null;
        try {
            if (pair.getContextChunks() != null && !pair.getContextChunks().isBlank()) {
                sourcesNode = objectMapper.readTree(pair.getContextChunks());
            }
        } catch (JsonProcessingException e) {
            log.error("Failed to parse context_chunks for QaPair {}", pair.getId(), e);
        }
        return new QaPairResponse(pair.getId(), pair.getQuestion(), pair.getAnswer(), sourcesNode, pair.getCreatedAt());
    }
    
    // Internal DTOs for JSON formatting
    private record RagQueryRequest(String userId, String question) {}
    private record ErrorEvent(String type, String message) {}
}
