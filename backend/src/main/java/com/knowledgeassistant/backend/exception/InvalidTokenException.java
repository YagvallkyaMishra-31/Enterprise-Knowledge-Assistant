package com.knowledgeassistant.backend.exception;

/** Thrown when a refresh token is invalid or expired. */
public class InvalidTokenException extends RuntimeException {
    public InvalidTokenException(String message) {
        super(message);
    }
}
