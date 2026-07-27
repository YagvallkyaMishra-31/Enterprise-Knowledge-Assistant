package com.knowledgeassistant.backend.service;

import com.knowledgeassistant.backend.dto.DocumentResponse;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;
import java.util.UUID;

/**
 * Business logic for document management.
 *
 * <p>All ownership checks are enforced here, never in the controller.</p>
 */
public interface DocumentService {

    /**
     * Uploads a document file and creates a PENDING database record.
     *
     * @param file   the uploaded multipart file
     * @param userId the authenticated user's ID
     * @return the created document's client-safe representation
     */
    DocumentResponse uploadDocument(MultipartFile file, UUID userId);

    /**
     * Lists all documents owned by the given user, newest first.
     *
     * @param userId the authenticated user's ID
     * @return list of document representations
     */
    List<DocumentResponse> listDocuments(UUID userId);

    /**
     * Retrieves a single document if owned by the requesting user.
     *
     * @param documentId the document ID
     * @param userId     the authenticated user's ID
     * @return the document's client-safe representation
     * @throws com.knowledgeassistant.backend.exception.DocumentNotFoundException
     *         if not found or not owned
     */
    DocumentResponse getDocument(UUID documentId, UUID userId);

    /**
     * Deletes a document (DB row and physical file) if owned by the requesting user.
     *
     * @param documentId the document ID
     * @param userId     the authenticated user's ID
     * @throws com.knowledgeassistant.backend.exception.DocumentNotFoundException
     *         if not found or not owned
     */
    void deleteDocument(UUID documentId, UUID userId);
}
