package com.knowledgeassistant.backend.exception;

/** Thrown when attempting to register with an email that is already taken. */
public class UserAlreadyExistsException extends RuntimeException {
    public UserAlreadyExistsException(String message) {
        super(message);
    }
}
