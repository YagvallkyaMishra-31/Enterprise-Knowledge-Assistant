package com.knowledgeassistant.backend.service.impl;

import com.knowledgeassistant.backend.config.JwtService;
import com.knowledgeassistant.backend.dto.AuthResponse;
import com.knowledgeassistant.backend.dto.LoginRequest;
import com.knowledgeassistant.backend.dto.RefreshRequest;
import com.knowledgeassistant.backend.dto.RegisterRequest;
import com.knowledgeassistant.backend.entity.RefreshToken;
import com.knowledgeassistant.backend.entity.User;
import com.knowledgeassistant.backend.exception.InvalidTokenException;
import com.knowledgeassistant.backend.exception.UserAlreadyExistsException;
import com.knowledgeassistant.backend.repository.RefreshTokenRepository;
import com.knowledgeassistant.backend.repository.UserRepository;
import com.knowledgeassistant.backend.service.AuthService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Instant;
import java.util.UUID;

/** Implementation of AuthService handling JWT generation, user persistence, and token rotation. */
@Service
public class AuthServiceImpl implements AuthService {

    private final UserRepository userRepository;
    private final RefreshTokenRepository refreshTokenRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;
    private final AuthenticationManager authenticationManager;

    @Value("${app.security.jwt.expiration-ms}")
    private long jwtExpirationMs;

    @Value("${app.security.jwt.refresh-expiration-ms}")
    private long jwtRefreshExpirationMs;

    public AuthServiceImpl(UserRepository userRepository, RefreshTokenRepository refreshTokenRepository,
                           PasswordEncoder passwordEncoder, JwtService jwtService,
                           AuthenticationManager authenticationManager) {
        this.userRepository = userRepository;
        this.refreshTokenRepository = refreshTokenRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
        this.authenticationManager = authenticationManager;
    }

    @Override
    @Transactional
    public AuthResponse register(RegisterRequest request) {
        if (userRepository.existsByEmail(request.email())) {
            throw new UserAlreadyExistsException("Email is already registered");
        }

        User user = User.builder()
                .email(request.email())
                .passwordHash(passwordEncoder.encode(request.password()))
                .displayName(request.fullName())
                .build();
        userRepository.save(user);

        return buildAuthResponse(user);
    }

    @Override
    @Transactional
    public AuthResponse login(LoginRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.email(), request.password())
        );

        User user = userRepository.findByEmail(request.email()).orElseThrow();
        refreshTokenRepository.deleteByUser(user); // Invalidates previous refresh tokens
        return buildAuthResponse(user);
    }

    @Override
    @Transactional
    public AuthResponse refresh(RefreshRequest request) {
        RefreshToken oldToken = refreshTokenRepository.findByToken(request.refreshToken())
                .orElseThrow(() -> new InvalidTokenException("Refresh token not found"));

        if (oldToken.getExpiryDate().isBefore(Instant.now())) {
            refreshTokenRepository.delete(oldToken);
            throw new InvalidTokenException("Refresh token has expired");
        }

        User user = oldToken.getUser();
        refreshTokenRepository.delete(oldToken); // Rotate the token

        return buildAuthResponse(user);
    }

    private AuthResponse buildAuthResponse(User user) {
        String accessToken = jwtService.generateToken(user.getEmail(), user.getId().toString());
        String refreshTokenString = UUID.randomUUID().toString();
        
        RefreshToken refreshToken = RefreshToken.builder()
                .user(user)
                .token(refreshTokenString)
                .expiryDate(Instant.now().plusMillis(jwtRefreshExpirationMs))
                .build();
        refreshTokenRepository.save(refreshToken);

        return new AuthResponse(accessToken, refreshTokenString, "Bearer", jwtExpirationMs);
    }
}
