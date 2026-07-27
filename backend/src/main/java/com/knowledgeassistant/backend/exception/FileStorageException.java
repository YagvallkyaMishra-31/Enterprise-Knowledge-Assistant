package com.knowledgeassistant.backend.exception;

/** Thrown when a file I/O operation fails during upload or deletion. */
public class FileStorageException extends RuntimeException {

    public FileStorageException(String message, Throwable cause) {
        super(message, cause);
    }
}
