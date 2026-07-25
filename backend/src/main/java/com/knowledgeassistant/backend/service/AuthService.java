package com.knowledgeassistant.backend.service;

import com.knowledgeassistant.backend.dto.AuthResponse;
import com.knowledgeassistant.backend.dto.LoginRequest;
import com.knowledgeassistant.backend.dto.RefreshRequest;
import com.knowledgeassistant.backend.dto.RegisterRequest;

/** Business logic for user authentication. */
public interface AuthService {
    AuthResponse register(RegisterRequest request);
    AuthResponse login(LoginRequest request);
    AuthResponse refresh(RefreshRequest request);
}
