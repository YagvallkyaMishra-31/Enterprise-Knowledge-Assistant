package com.knowledgeassistant.backend.service;

import java.util.UUID;

/**
 * Service for integrating with the RAG processing pipeline.
 */
public interface RagIntegrationService {

    /**
     * Triggers the Python RAG service to process a document asynchronously.
     *
     * @param documentId the UUID of the document
     * @param userId     the UUID of the owner
     * @param filePath   the relative path of the stored file
     */
    void triggerProcessing(UUID documentId, UUID userId, String filePath);
}
