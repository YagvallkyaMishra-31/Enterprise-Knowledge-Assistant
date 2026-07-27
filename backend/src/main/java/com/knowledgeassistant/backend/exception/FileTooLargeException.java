package com.knowledgeassistant.backend.exception;

/** Thrown when an uploaded file exceeds the configured maximum size. */
public class FileTooLargeException extends RuntimeException {

    public FileTooLargeException(String message) {
        super(message);
    }
}
