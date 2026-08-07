package com.knowledgeassistant.backend.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Unit tests for {@link JwtService}.
 *
 * <p>Uses reflection to inject the {@code @Value} fields directly,
 * avoiding the need for a Spring application context or a running database.</p>
 */
class JwtServiceTest {

    // A valid 256-bit base64-encoded key for HS256 signing.
    private static final String TEST_SECRET =
            "dGhpcyBpcyBhIHN1ZmZpY2llbnRseSBsb25nIHNlY3JldCBrZXkgZm9yIEhTMjU2";
    private static final long TEST_EXPIRATION_MS = 600_000; // 10 minutes

    private JwtService jwtService;

    @BeforeEach
    void setUp() throws Exception {
        jwtService = new JwtService();
        setField(jwtService, "secretKey", TEST_SECRET);
        setField(jwtService, "jwtExpiration", TEST_EXPIRATION_MS);
    }

    /**
     * Verifies that a generated token contains the correct subject (username)
     * and custom userId claim, that it is not expired, and that
     * {@link JwtService#isTokenValid} accepts it.
     *
     * <p>This catches regressions in claim key names, signing configuration,
     * and expiration logic — all of which are real security-critical paths.</p>
     */
    @Test
    void generateToken_containsExpectedClaimsAndIsValid() {
        String username = "alice@example.com";
        String userId = UUID.randomUUID().toString();

        String token = jwtService.generateToken(username, userId);

        // Parse the token independently to inspect claims
        Claims claims = Jwts.parser()
                .verifyWith(Keys.hmacShaKeyFor(Decoders.BASE64.decode(TEST_SECRET)))
                .build()
                .parseSignedClaims(token)
                .getPayload();

        assertEquals(username, claims.getSubject(),
                "Token subject must match the username it was generated for");
        assertEquals(userId, claims.get("userId", String.class),
                "Token must carry the userId as a custom claim");
        assertTrue(claims.getExpiration().getTime() > System.currentTimeMillis(),
                "Token must not be expired immediately after generation");

        // Confirm the service's own validation accepts the token
        assertTrue(jwtService.isTokenValid(token, username),
                "isTokenValid must return true for a freshly generated token");

        // Confirm validation rejects a different username
        assertFalse(jwtService.isTokenValid(token, "mallory@example.com"),
                "isTokenValid must reject a token when checked against a different username");
    }

    /** Sets a private field on an object via reflection. */
    private static void setField(Object target, String fieldName, Object value) throws Exception {
        Field field = target.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(target, value);
    }
}
