package com.knowledgeassistant.backend.controller;

import com.knowledgeassistant.backend.config.CustomUserDetails;
import com.knowledgeassistant.backend.dto.chat.AskRequest;
import com.knowledgeassistant.backend.service.ChatService;
import jakarta.validation.Valid;
import org.springframework.http.MediaType;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.UUID;

/** REST endpoint for streaming RAG chat queries. */
@RestController
@RequestMapping("/api/chat/sessions")
public class ChatController {

    private final ChatService chatService;

    public ChatController(ChatService chatService) {
        this.chatService = chatService;
    }

    /**
     * Initiates a streaming RAG query for a specific session.
     * Produces Server-Sent Events (SSE).
     */
    @PostMapping(value = "/{id}/ask", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter askQuestionStream(
            @PathVariable UUID id,
            @Valid @RequestBody AskRequest request,
            @AuthenticationPrincipal CustomUserDetails principal) {
        return chatService.askQuestionStream(id, principal.getId(), request.question());
    }
}
