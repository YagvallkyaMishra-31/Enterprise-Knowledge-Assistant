package com.knowledgeassistant.backend.dto;

/** Response payload returning authentication tokens. */
public record AuthResponse(
        String accessToken,
        String refreshToken,
        String tokenType,
        long expiresIn
) {}
