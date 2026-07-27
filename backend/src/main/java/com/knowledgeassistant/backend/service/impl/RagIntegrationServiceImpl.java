package com.knowledgeassistant.backend.service.impl;

import com.knowledgeassistant.backend.service.RagIntegrationService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Implementation of RagIntegrationService for triggering the Python pipeline.
 */
@Service
public class RagIntegrationServiceImpl implements RagIntegrationService {

    private static final Logger log = LoggerFactory.getLogger(RagIntegrationServiceImpl.class);

    private final RestTemplate restTemplate;
    private final String ragServiceUrl;
    private final String internalApiKey;

    public RagIntegrationServiceImpl(
            RestTemplate restTemplate,
            @Value("${app.rag-service-url}") String ragServiceUrl,
            @Value("${app.internal-api-key}") String internalApiKey) {
        this.restTemplate = restTemplate;
        this.ragServiceUrl = ragServiceUrl;
        this.internalApiKey = internalApiKey;
    }

    @Override
    @Async("ragServiceExecutor")
    public void triggerProcessing(UUID documentId, UUID userId, String filePath) {
        String url = ragServiceUrl + "/internal/process-document";
        
        HttpHeaders headers = new HttpHeaders();
        headers.set("X-Internal-Api-Key", internalApiKey);
        headers.set("Content-Type", "application/json");

        Map<String, String> body = new HashMap<>();
        body.put("documentId", documentId.toString());
        body.put("userId", userId.toString());
        body.put("filePath", filePath);

        HttpEntity<Map<String, String>> request = new HttpEntity<>(body, headers);

        try {
            log.info("Triggering RAG pipeline for documentId={}", documentId);
            restTemplate.exchange(url, HttpMethod.POST, request, String.class);
            log.info("RAG pipeline triggered successfully for documentId={}", documentId);
        } catch (Exception e) {
            log.error("Failed to trigger RAG pipeline for documentId={}. Error: {}", documentId, e.getMessage());
            // Document status remains PENDING.
        }
    }
}
