# ── Build stage ─────────────────────────────────────
FROM maven:3.9-eclipse-temurin-21 AS build
WORKDIR /build

# Sophos SSL inspection intercepts HTTPS inside Docker containers.
# Extract the FULL certificate chain as seen by this container and
# import every cert into the JDK truststore so Maven can download.
RUN apt-get update -qq && apt-get install -y -qq openssl > /dev/null 2>&1 && \
    echo | openssl s_client -showcerts -servername repo.maven.apache.org \
      -connect repo.maven.apache.org:443 2>/dev/null \
    | awk 'BEGIN{n=0} /-----BEGIN CERTIFICATE-----/{n++; f="/tmp/cert-"n".pem"} n>0{print > f}' && \
    for cert in /tmp/cert-*.pem; do \
      alias="proxy-ca-$(basename "$cert" .pem)"; \
      keytool -import -trustcacerts \
        -keystore "$JAVA_HOME/lib/security/cacerts" \
        -storepass changeit -noprompt \
        -alias "$alias" -file "$cert" 2>/dev/null || true; \
    done && \
    rm -f /tmp/cert-*.pem

COPY pom.xml .
RUN mvn dependency:go-offline -B
COPY src ./src
RUN mvn package -DskipTests -B

# ── Runtime stage ──────────────────────────────────
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /build/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
