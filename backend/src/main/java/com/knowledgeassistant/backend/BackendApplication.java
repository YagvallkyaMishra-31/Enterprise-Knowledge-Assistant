package com.knowledgeassistant.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/** Entry point for the Knowledge Assistant orchestration and persistence service. */
@SpringBootApplication
public class BackendApplication {

    public static void main(String[] args) {
        // Fix for DNS caching artifact when Docker containers restart
        java.security.Security.setProperty("networkaddress.cache.ttl", "5");
        java.security.Security.setProperty("networkaddress.cache.negative.ttl", "2");
        
        SpringApplication.run(BackendApplication.class, args);
    }
}
