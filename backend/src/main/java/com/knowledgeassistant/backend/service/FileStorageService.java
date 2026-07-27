package com.knowledgeassistant.backend.service;

import org.springframework.web.multipart.MultipartFile;

import java.util.UUID;

/**
 * Abstraction for document file storage.
 *
 * <p>The interface exists so the storage backend (local disk today, S3-compatible
 * tomorrow) can be swapped without touching business logic.</p>
 */
public interface FileStorageService {

    /**
     * Persists the uploaded file to storage, scoped under the given user.
     *
     * @param file   the uploaded multipart file
     * @param userId the owner's ID, used as a subdirectory
     * @return the relative path of the stored file (from the upload root)
     */
    String store(MultipartFile file, UUID userId);

    /**
     * Deletes a previously stored file.
     *
     * @param storedPath the relative path returned by {@link #store}
     */
    void delete(String storedPath);
}
