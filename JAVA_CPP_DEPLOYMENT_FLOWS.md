# PromptOps: Java & C++ Application Deployment Flows
## Complete Guide for Compiled Languages

**Version 1.0 | May 2026**  
**Compiled Language Deployment Specialization**

---

## Table of Contents

1. [Language Detection & Build Tool Recognition](#language-detection--build-tool-recognition)
2. [Java Application Deployments](#java-application-deployments)
3. [C++ Application Deployments](#c-application-deployments)
4. [Build Pipeline Comparison](#build-pipeline-comparison)
5. [Mixed-Language Applications](#mixed-language-applications)
6. [Performance Optimizations](#performance-optimizations)

---

## Language Detection & Build Tool Recognition

### How PromptOps Detects Your Application Stack

```
PM Command: "Deploy payment-processor v3.5 to production with canary"
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 1: NLP Parser + Code Repository Analysis                   │
└─────────────────────────────────────────────────────────────────┘

NLP Parser
├─ Extracts: app="payment-processor", version="3.5", env="production"
└─ Queries Infrastructure Context Store
        │
        ▼
Infrastructure Context Store (DynamoDB)
├─ Application: payment-processor
├─ Repository: github.com/company/payment-processor
├─ Primary Language: Java
├─ Build Tool: Maven
├─ Framework: Spring Boot 3.2
├─ JDK Version: 17
├─ Deployment Target: ECS Fargate
├─ Last Deployment: v3.4 (2026-04-28)
└─ Build Time Avg: 12 minutes
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: CI/CD Agent Language-Specific Pipeline Selection        │
└─────────────────────────────────────────────────────────────────┘

Pipeline Decision Engine
├─ Language: Java
├─ Build Tool: Maven
├─ Pipeline Selection: Jenkins (Maven + SonarQube required for SOX)
├─ Estimated Build Time: 12 minutes
├─ Container Base Image: eclipse-temurin:17-jre-alpine
└─ Deployment Strategy: Canary (enterprise path)
```

### Build Tool Auto-Detection Logic

```python
# api_gateway/agents/cicd_agent.py

class BuildToolDetector:
    """
    Automatically detects build tools and language ecosystems
    by analyzing repository structure.
    """
    
    def detect_build_system(self, repo_path: str) -> Dict:
        """
        Scans repository for build configuration files.
        Returns detected language, build tool, and configuration.
        """
        
        detections = []
        
        # Java Build Tools
        if os.path.exists(f"{repo_path}/pom.xml"):
            detections.append({
                "language": "java",
                "build_tool": "maven",
                "config_file": "pom.xml",
                "confidence": 0.99
            })
        
        if os.path.exists(f"{repo_path}/build.gradle") or \
           os.path.exists(f"{repo_path}/build.gradle.kts"):
            detections.append({
                "language": "java",
                "build_tool": "gradle",
                "config_file": "build.gradle",
                "confidence": 0.99
            })
        
        # C++ Build Tools
        if os.path.exists(f"{repo_path}/CMakeLists.txt"):
            detections.append({
                "language": "cpp",
                "build_tool": "cmake",
                "config_file": "CMakeLists.txt",
                "confidence": 0.95
            })
        
        if os.path.exists(f"{repo_path}/Makefile"):
            detections.append({
                "language": "cpp",  # or C
                "build_tool": "make",
                "config_file": "Makefile",
                "confidence": 0.90
            })
        
        if os.path.exists(f"{repo_path}/conanfile.txt") or \
           os.path.exists(f"{repo_path}/conanfile.py"):
            detections.append({
                "language": "cpp",
                "build_tool": "conan",
                "dependency_manager": True,
                "config_file": "conanfile.txt",
                "confidence": 0.95
            })
        
        if os.path.exists(f"{repo_path}/BUILD") or \
           os.path.exists(f"{repo_path}/WORKSPACE"):
            detections.append({
                "language": "cpp",  # or Java, or multi-language
                "build_tool": "bazel",
                "config_file": "BUILD",
                "confidence": 0.98
            })
        
        # Analyze language prevalence in source files
        source_files = self._scan_source_files(repo_path)
        
        # Return primary build system
        if detections:
            primary = max(detections, key=lambda x: x['confidence'])
            
            # Enrich with source file analysis
            primary['source_file_count'] = source_files.get(primary['language'], 0)
            primary['jdk_version'] = self._detect_java_version(repo_path)
            primary['cpp_standard'] = self._detect_cpp_standard(repo_path)
            
            return primary
        
        # Default: assume Dockerfile exists
        return {
            "language": "unknown",
            "build_tool": "docker",
            "config_file": "Dockerfile"
        }
    
    def _detect_java_version(self, repo_path: str) -> str:
        """Extract JDK version from pom.xml or gradle.properties"""
        
        pom_path = f"{repo_path}/pom.xml"
        if os.path.exists(pom_path):
            with open(pom_path) as f:
                content = f.read()
                # Extract <java.version>17</java.version>
                match = re.search(r'<java\.version>(\d+)</java\.version>', content)
                if match:
                    return match.group(1)
                
                # Extract <maven.compiler.source>17</maven.compiler.source>
                match = re.search(r'<maven\.compiler\.source>(\d+)</maven\.compiler\.source>', content)
                if match:
                    return match.group(1)
        
        return "17"  # Default to LTS
    
    def _detect_cpp_standard(self, repo_path: str) -> str:
        """Extract C++ standard from CMakeLists.txt"""
        
        cmake_path = f"{repo_path}/CMakeLists.txt"
        if os.path.exists(cmake_path):
            with open(cmake_path) as f:
                content = f.read()
                # Extract set(CMAKE_CXX_STANDARD 17)
                match = re.search(r'CMAKE_CXX_STANDARD\s+(\d+)', content)
                if match:
                    return f"C++{match.group(1)}"
        
        return "C++17"  # Default
```

---

## Java Application Deployments

### Flow 1: Java Spring Boot Microservice (Maven + Jenkins)

```
PM Command: "Deploy payment-processor v3.5 to production with canary"
        │
        ▼
Detection Results:
├─ Language: Java
├─ Build Tool: Maven 3.9
├─ Framework: Spring Boot 3.2.0
├─ JDK: 17 (Temurin)
├─ Dependencies: 127 (from pom.xml)
├─ Tests: JUnit 5 + Mockito
└─ Packaging: JAR (executable)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Jenkins Pipeline: PromptOps-Java-Maven-Canary-Deploy            │
└─────────────────────────────────────────────────────────────────┘

Stage 1: Environment Setup (1 minute)
├─ Agent: linux-docker-maven
├─ Pull Docker image: maven:3.9-eclipse-temurin-17
├─ Checkout code: git checkout tags/v3.5
└─ Verify Maven wrapper: ./mvnw --version
        │
        ▼
Stage 2: Dependency Resolution (3 minutes)
├─ Download dependencies from Maven Central
│   └─ Command: ./mvnw dependency:resolve
├─ Download plugins
│   └─ Command: ./mvnw dependency:resolve-plugins
├─ Cache dependencies (speeds up future builds)
│   └─ ~/.m2/repository → Jenkins cache
└─ Dependency tree analysis (security scan preparation)
    └─ Command: ./mvnw dependency:tree > dependencies.txt
        │
        ▼
Stage 3: Compile & Package (5 minutes)
├─ Clean previous builds
│   └─ Command: ./mvnw clean
├─ Compile source code
│   └─ Command: ./mvnw compile
│       ├─ Compiled: 1,234 classes
│       ├─ Resources: 45 files (application.yml, logback.xml, etc.)
│       └─ Duration: 2m 15s
├─ Run unit tests (parallel execution)
│   └─ Command: ./mvnw test
│       ├─ Tests run: 2,456
│       ├─ Failures: 0
│       ├─ Errors: 0
│       ├─ Skipped: 0
│       ├─ Coverage: 87.3% (JaCoCo)
│       └─ Duration: 1m 45s
├─ Package JAR
│   └─ Command: ./mvnw package -DskipTests
│       ├─ Output: target/payment-processor-3.5.jar (75 MB)
│       ├─ Type: Spring Boot executable JAR (fat JAR with embedded Tomcat)
│       └─ Duration: 1m 20s
└─ Generate build artifacts
    ├─ JAR file: payment-processor-3.5.jar
    ├─ POM file: pom.xml
    ├─ Dependency list: dependencies.txt
    └─ Test reports: target/surefire-reports/
        │
        ▼
Stage 4: Code Quality & Security Analysis (4 minutes)
├─ SonarQube Analysis (SAST - Static Application Security Testing)
│   └─ Command: ./mvnw sonar:sonar \
│         -Dsonar.projectKey=payment-processor \
│         -Dsonar.host.url=https://sonarqube.company.com \
│         -Dsonar.login=$SONAR_TOKEN
│       ├─ Lines of Code: 45,678
│       ├─ Code Smells: 23 (minor)
│       ├─ Bugs: 0
│       ├─ Vulnerabilities: 0
│       ├─ Security Hotspots: 2 (reviewed)
│       ├─ Coverage: 87.3%
│       ├─ Duplications: 1.2%
│       └─ Quality Gate: PASSED ✓
│
├─ OWASP Dependency Check (vulnerable dependencies)
│   └─ Command: ./mvnw dependency-check:check \
│         -DfailBuildOnCVSS=7
│       ├─ Dependencies scanned: 127
│       ├─ CVEs found: 0 critical, 0 high, 2 medium
│       └─ Result: PASSED ✓
│
├─ Checkmarx SAST (deep security analysis)
│   └─ Command: cx scan create \
│         --project payment-processor \
│         --branch v3.5 \
│         --severity HIGH,CRITICAL
│       ├─ Files scanned: 1,234
│       ├─ Findings: 0 critical, 0 high
│       └─ Result: PASSED ✓
│
└─ License Compliance Check
    └─ Command: ./mvnw license:check
        ├─ Licenses: Apache-2.0 (95%), MIT (5%)
        ├─ Blacklisted licenses: 0
        └─ Result: PASSED ✓
        │
        ▼
Stage 5: Integration Tests (7 minutes)
├─ Start test infrastructure (Docker Compose)
│   └─ Command: docker-compose -f docker-compose.test.yml up -d
│       ├─ PostgreSQL 15: localhost:5432
│       ├─ Redis 7: localhost:6379
│       ├─ Kafka 3.5: localhost:9092
│       └─ WireMock (API mocks): localhost:8080
│
├─ Run integration tests
│   └─ Command: ./mvnw verify \
│         -Dspring.profiles.active=test \
│         -Dtest.database.url=jdbc:postgresql://localhost:5432/test
│       ├─ Integration tests: 89
│       ├─ Passed: 89
│       ├─ Duration: 5m 30s
│       ├─ Database migrations tested: 43
│       └─ API endpoints tested: 127
│
├─ Performance test (JMeter)
│   └─ Command: jmeter -n \
│         -t payment-processor-load-test.jmx \
│         -l results.jtl \
│         -Jthreads=100 \
│         -Jduration=60
│       ├─ Total requests: 6,000
│       ├─ Throughput: 100 req/sec
│       ├─ Avg response time: 45ms
│       ├─ P95 response time: 120ms
│       ├─ P99 response time: 250ms
│       ├─ Error rate: 0.02%
│       └─ Result: PASSED ✓
│
└─ Stop test infrastructure
    └─ Command: docker-compose -f docker-compose.test.yml down
        │
        ▼
Stage 6: Container Build (Multi-stage Docker) (3 minutes)
├─ Create optimized Dockerfile
│   └─ Dockerfile.java-maven:
│       ```dockerfile
│       # Stage 1: Build (already done by Maven)
│       # We just copy the JAR
│       
│       # Stage 2: Runtime
│       FROM eclipse-temurin:17-jre-alpine
│       
│       # Add non-root user for security
│       RUN addgroup -S spring && adduser -S spring -G spring
│       USER spring:spring
│       
│       # Copy JAR from Maven build
│       ARG JAR_FILE=target/payment-processor-3.5.jar
│       COPY ${JAR_FILE} app.jar
│       
│       # Expose port
│       EXPOSE 8080
│       
│       # JVM tuning for containers
│       ENV JAVA_OPTS="-XX:+UseContainerSupport \
│                      -XX:MaxRAMPercentage=75.0 \
│                      -XX:+UseG1GC \
│                      -XX:+UseStringDeduplication \
│                      -Djava.security.egd=file:/dev/./urandom"
│       
│       # Health check
│       HEALTHCHECK --interval=30s --timeout=3s --start-period=60s \
│         CMD wget --no-verbose --tries=1 --spider http://localhost:8080/actuator/health || exit 1
│       
│       # Run application
│       ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app.jar"]
│       ```
│
├─ Build Docker image
│   └─ Command: docker build \
│         -t payment-processor:3.5 \
│         -f Dockerfile.java-maven .
│       ├─ Base image size: 180 MB (Temurin JRE Alpine)
│       ├─ Application layer: 75 MB (fat JAR)
│       ├─ Total image size: 255 MB
│       └─ Build time: 2m 15s
│
├─ Tag for registries
│   └─ Commands:
│       ├─ docker tag payment-processor:3.5 \
│           company.jfrog.io/payment-processor:3.5
│       └─ docker tag payment-processor:3.5 \
│           123456789.dkr.ecr.us-east-1.amazonaws.com/payment-processor:3.5
│
├─ Container security scan (Trivy)
│   └─ Command: trivy image \
│         --severity HIGH,CRITICAL \
│         --exit-code 1 \
│         payment-processor:3.5
│       ├─ Vulnerabilities: 0 critical, 0 high
│       ├─ OS packages scanned: 15 (Alpine)
│       └─ Result: PASSED ✓
│
└─ Push to registries
    ├─ Push to JFrog Artifactory (primary)
    │   └─ Command: docker push company.jfrog.io/payment-processor:3.5
    └─ Push to AWS ECR (for ECS deployment)
        └─ Command: docker push \
              123456789.dkr.ecr.us-east-1.amazonaws.com/payment-processor:3.5
        │
        ▼
Stage 7-11: Canary Deployment (90 minutes)
├─ Same as standard PromptOps canary flow
├─ Deploy 5% → Monitor 30 min
├─ Deploy 25% → Monitor 30 min
├─ Deploy 50% → Monitor 30 min
└─ Deploy 100% → Complete
        │
        ▼
✅ Java Deployment Complete
Duration: 25 minutes (build + test) + 90 minutes (canary) = 115 minutes
Artifact: 255 MB Docker image with JRE 17 + 75 MB JAR
```

---

### Flow 2: Java Gradle Microservice (Kotlin DSL + GitHub Actions)

```
PM Command: "Deploy user-service v2.1 to staging"
        │
        ▼
Detection Results:
├─ Language: Java + Kotlin
├─ Build Tool: Gradle 8.5 (Kotlin DSL)
├─ Framework: Spring Boot 3.2
├─ JDK: 17
├─ Build File: build.gradle.kts
└─ Environment: staging (non-critical) → GitHub Actions (fast path)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ GitHub Actions: .github/workflows/deploy-java-gradle.yml        │
└─────────────────────────────────────────────────────────────────┘

name: Deploy Java Gradle Application

on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to deploy'
        required: true
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          ref: v${{ inputs.version }}
      
      - name: Set up JDK 17
        uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
          cache: 'gradle'  # Caches ~/.gradle/caches and ~/.gradle/wrapper
      
      - name: Grant execute permission for gradlew
        run: chmod +x gradlew
      
      - name: Build with Gradle
        run: ./gradlew clean build --no-daemon --parallel
        # --no-daemon: Don't start Gradle daemon (CI best practice)
        # --parallel: Parallel project execution
      
      - name: Run tests
        run: ./gradlew test --no-daemon
      
      - name: Generate test report
        if: always()
        uses: dorny/test-reporter@v1
        with:
          name: Gradle Tests
          path: build/test-results/test/*.xml
          reporter: java-junit
      
      - name: Build Docker image
        run: |
          docker build -t user-service:${{ inputs.version }} .
          docker tag user-service:${{ inputs.version }} \
            123456789.dkr.ecr.us-east-1.amazonaws.com/user-service:${{ inputs.version }}
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to Amazon ECR
        run: |
          aws ecr get-login-password --region us-east-1 | \
            docker login --username AWS --password-stdin \
            123456789.dkr.ecr.us-east-1.amazonaws.com
      
      - name: Push Docker image
        run: |
          docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/user-service:${{ inputs.version }}
      
      - name: Deploy to ECS Staging
        run: |
          aws ecs update-service \
            --cluster staging \
            --service user-service \
            --force-new-deployment \
            --task-definition user-service:${{ inputs.version }}
      
      - name: Wait for deployment to stabilize
        run: |
          aws ecs wait services-stable \
            --cluster staging \
            --services user-service \
            --timeout 600
      
      - name: Notify PromptOps
        run: |
          curl -X POST http://promptops-api/deployments/status \
            -H 'Content-Type: application/json' \
            -d '{
              "deployment_id": "${{ github.run_id }}",
              "application": "user-service",
              "version": "${{ inputs.version }}",
              "environment": "${{ inputs.environment }}",
              "status": "success",
              "duration_seconds": ${{ job.duration }},
              "pipeline": "github-actions"
            }'

Duration: 8 minutes (Gradle is faster than Maven due to incremental builds)
✅ Staging deployment complete
```

---

## C++ Application Deployments

### Flow 3: C++ High-Performance Service (CMake + Conan + Jenkins)

```
PM Command: "Deploy trading-engine v1.8 to production with blue-green"
        │
        ▼
Detection Results:
├─ Language: C++17
├─ Build Tool: CMake 3.27
├─ Dependency Manager: Conan 2.0
├─ Compiler: GCC 11 (Linux) / Clang 15 (macOS)
├─ Framework: Custom (low-latency trading)
├─ Dependencies: 23 (Boost, gRPC, Protobuf, etc.)
├─ Build Type: Release (optimizations: -O3 -march=native)
└─ Target: x86_64 Linux (bare metal or ECS)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Jenkins Pipeline: PromptOps-CPP-CMake-BlueGreen-Deploy          │
└─────────────────────────────────────────────────────────────────┘

Stage 1: Build Environment Setup (2 minutes)
├─ Agent: linux-cpp-build-server
│   ├─ CPU: 32 cores (for parallel compilation)
│   ├─ RAM: 64 GB
│   ├─ Compiler: GCC 11.4
│   └─ CMake: 3.27
├─ Checkout code: git checkout tags/v1.8
├─ Install Conan (if not cached)
│   └─ Command: pip install conan==2.0.13
└─ Verify toolchain
    ├─ g++ --version → 11.4.0
    ├─ cmake --version → 3.27.0
    └─ conan --version → 2.0.13
        │
        ▼
Stage 2: Dependency Management (5 minutes)
├─ Parse Conan dependencies (conanfile.txt)
│   └─ Contents:
│       ```ini
│       [requires]
│       boost/1.82.0
│       grpc/1.54.0
│       protobuf/3.21.12
│       fmt/10.1.1
│       spdlog/1.12.0
│       catch2/3.4.0
│       
│       [generators]
│       CMakeDeps
│       CMakeToolchain
│       
│       [options]
│       boost:shared=False
│       grpc:shared=False
│       ```
│
├─ Install dependencies via Conan
│   └─ Command: conan install . \
│         --output-folder=build \
│         --build=missing \
│         --settings=build_type=Release \
│         --settings=compiler=gcc \
│         --settings=compiler.version=11 \
│         --settings=compiler.libcxx=libstdc++11 \
│         --settings=arch=x86_64
│       ├─ Cache hit: 18 packages (pre-built binaries from Artifactory)
│       ├─ Cache miss: 5 packages (build from source)
│       ├─ Building boost: 3m 20s (parallel compilation -j32)
│       ├─ Building grpc: 1m 45s
│       └─ Total: 4m 50s
│
└─ Generate dependency graph
    └─ Command: conan graph info . --format=html > deps.html
        │
        ▼
Stage 3: CMake Configuration (1 minute)
├─ Configure CMake build
│   └─ Command: cmake -S . -B build \
│         -DCMAKE_BUILD_TYPE=Release \
│         -DCMAKE_TOOLCHAIN_FILE=build/conan_toolchain.cmake \
│         -DCMAKE_CXX_STANDARD=17 \
│         -DCMAKE_CXX_FLAGS="-O3 -march=native -Wall -Werror" \
│         -DENABLE_TESTING=ON
│       ├─ Generator: Unix Makefiles
│       ├─ C++ compiler: /usr/bin/g++
│       ├─ C++ standard: 17
│       ├─ Build type: Release
│       ├─ Optimization flags: -O3 -march=native
│       ├─ Dependencies found: 23 (via Conan)
│       └─ Configuration time: 45s
│
└─ CMakeLists.txt structure:
    ```cmake
    cmake_minimum_required(VERSION 3.27)
    project(TradingEngine VERSION 1.8.0 LANGUAGES CXX)
    
    set(CMAKE_CXX_STANDARD 17)
    set(CMAKE_CXX_STANDARD_REQUIRED ON)
    
    # Find dependencies from Conan
    find_package(Boost REQUIRED COMPONENTS system thread)
    find_package(gRPC REQUIRED)
    find_package(Protobuf REQUIRED)
    find_package(fmt REQUIRED)
    find_package(spdlog REQUIRED)
    
    # Source files
    file(GLOB_RECURSE SOURCES src/*.cpp)
    file(GLOB_RECURSE HEADERS include/*.hpp)
    
    # Main executable
    add_executable(trading-engine ${SOURCES})
    
    target_include_directories(trading-engine
        PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include
    )
    
    target_link_libraries(trading-engine
        PRIVATE
            Boost::system
            Boost::thread
            gRPC::grpc++
            protobuf::libprotobuf
            fmt::fmt
            spdlog::spdlog
    )
    
    # Enable warnings
    target_compile_options(trading-engine PRIVATE -Wall -Wextra -Werror)
    
    # Tests
    if(ENABLE_TESTING)
        enable_testing()
        add_subdirectory(tests)
    endif()
    ```
        │
        ▼
Stage 4: Compilation (8 minutes)
├─ Compile C++ source code (parallel)
│   └─ Command: cmake --build build --config Release --parallel 32
│       ├─ Compiling: 456 .cpp files
│       ├─ Linking: 1 executable (trading-engine)
│       ├─ Parallel jobs: 32 (one per core)
│       ├─ Compilation warnings: 0
│       ├─ Compilation errors: 0
│       ├─ Binary size: 24 MB (before strip)
│       ├─ Binary size: 12 MB (after strip -s)
│       └─ Duration: 7m 30s
│
├─ Symbol stripping (reduce binary size)
│   └─ Command: strip build/trading-engine
│       ├─ Before: 24 MB
│       └─ After: 12 MB
│
└─ Generate build artifacts
    ├─ Executable: build/trading-engine
    ├─ Debug symbols: build/trading-engine.debug
    ├─ Dependency list: build/deps.html
    └─ Compile commands: build/compile_commands.json
        │
        ▼
Stage 5: Unit Testing (3 minutes)
├─ Run unit tests (Catch2 framework)
│   └─ Command: ctest --test-dir build --output-on-failure -j32
│       ├─ Tests discovered: 1,234
│       ├─ Tests passed: 1,234
│       ├─ Tests failed: 0
│       ├─ Duration: 2m 45s
│       └─ Coverage: 89.2% (gcov)
│
├─ Memory leak check (Valgrind)
│   └─ Command: valgrind --leak-check=full \
│         --show-leak-kinds=all \
│         ./build/trading-engine --test-mode
│       ├─ Heap allocations: 45,678
│       ├─ Heap deallocations: 45,678
│       ├─ Leaked bytes: 0 ✓
│       └─ Duration: 15s
│
└─ Performance benchmarks (Google Benchmark)
    └─ Command: ./build/benchmarks --benchmark_format=json > bench.json
        ├─ Order processing latency: 2.3 μs (p50), 4.1 μs (p99)
        ├─ Market data throughput: 1.2M messages/sec
        └─ Memory footprint: 128 MB (resident)
        │
        ▼
Stage 6: Static Analysis (5 minutes)
├─ Clang-Tidy (C++ linter)
│   └─ Command: clang-tidy -p build src/*.cpp \
│         -checks='*,-fuchsia-*,-google-*'
│       ├─ Files analyzed: 456
│       ├─ Warnings: 12 (readability)
│       ├─ Errors: 0
│       └─ Result: PASSED ✓
│
├─ Cppcheck (static analysis)
│   └─ Command: cppcheck --enable=all \
│         --inconclusive \
│         --std=c++17 \
│         --error-exitcode=1 \
│         src/
│       ├─ Files checked: 456
│       ├─ Style issues: 5
│       ├─ Performance issues: 0
│       ├─ Errors: 0
│       └─ Result: PASSED ✓
│
└─ SonarQube C++ Analysis
    └─ Command: sonar-scanner \
          -Dsonar.projectKey=trading-engine \
          -Dsonar.sources=src \
          -Dsonar.cfamily.compile-commands=build/compile_commands.json
        ├─ Lines of code: 67,890
        ├─ Bugs: 0
        ├─ Vulnerabilities: 0
        ├─ Code smells: 15 (minor)
        └─ Quality Gate: PASSED ✓
        │
        ▼
Stage 7: Integration Testing (10 minutes)
├─ Start test environment
│   └─ Docker Compose:
│       ├─ PostgreSQL (market data store)
│       ├─ Redis (order cache)
│       ├─ Kafka (event stream)
│       └─ Mock exchange API
│
├─ Run integration tests
│   └─ Command: ./build/integration-tests --gtest_output=xml:results.xml
│       ├─ Test scenarios: 67
│       ├─ Passed: 67
│       ├─ Failed: 0
│       ├─ Duration: 8m 30s
│       └─ Test coverage:
│           ├─ Order placement → execution: ✓
│           ├─ Risk checks: ✓
│           ├─ Market data ingestion: ✓
│           └─ Position reconciliation: ✓
│
└─ Load testing (stress test)
    └─ Custom C++ load generator:
        ├─ Simulated orders: 10 million
        ├─ Throughput achieved: 1.2M orders/sec
        ├─ Latency p50: 2.1 μs
        ├─ Latency p99: 4.3 μs
        ├─ CPU usage: 65% (avg)
        └─ Result: PASSED ✓
        │
        ▼
Stage 8: Container Build (Distroless Base) (4 minutes)
├─ Create optimized Dockerfile
│   └─ Dockerfile.cpp-distroless:
│       ```dockerfile
│       # Stage 1: Build (already done by CMake)
│       # We just copy the binary
│       
│       # Stage 2: Runtime (Distroless - minimal attack surface)
│       FROM gcr.io/distroless/cc-debian11
│       
│       # Copy binary
│       COPY build/trading-engine /app/trading-engine
│       
│       # Copy runtime dependencies (if dynamic linking)
│       # COPY /usr/lib/x86_64-linux-gnu/libboost_system.so.1.82.0 /usr/lib/
│       
│       # Copy configuration files
│       COPY config/ /app/config/
│       
│       # Expose ports
│       EXPOSE 8080 9090
│       
│       # Run as non-root user (distroless already has 'nonroot' user)
│       USER nonroot:nonroot
│       
│       WORKDIR /app
│       
│       # Health check (use grpc_health_probe)
│       COPY grpc_health_probe /app/
│       HEALTHCHECK --interval=10s --timeout=3s --start-period=5s \
│         CMD ["/app/grpc_health_probe", "-addr=:9090"]
│       
│       # Run application
│       ENTRYPOINT ["/app/trading-engine"]
│       ```
│
├─ Build Docker image
│   └─ Command: docker build \
│         -t trading-engine:1.8 \
│         -f Dockerfile.cpp-distroless .
│       ├─ Base image size: 20 MB (distroless cc)
│       ├─ Application binary: 12 MB (stripped)
│       ├─ Configuration: 1 MB
│       ├─ Total image size: 33 MB (extremely lightweight!)
│       └─ Build time: 1m 30s
│
├─ Container security scan
│   └─ Command: trivy image trading-engine:1.8
│       ├─ Vulnerabilities: 0 (distroless has minimal packages)
│       └─ Result: PASSED ✓
│
└─ Push to ECR
    └─ Command: docker push \
          123456789.dkr.ecr.us-east-1.amazonaws.com/trading-engine:1.8
        │
        ▼
Stage 9-10: Blue-Green Deployment (15 minutes)
├─ Deploy to Green environment (isolated ECS cluster)
│   ├─ Launch 10 ECS tasks (c6i.8xlarge instances for low latency)
│   └─ Wait for health checks (5 min)
├─ Smoke tests on Green
│   ├─ gRPC health check: ✓
│   ├─ Order placement test: ✓
│   └─ Latency benchmark: 2.4 μs (acceptable) ✓
├─ Switch ALB traffic (Blue → Green)
│   └─ Instant cutover (no gradual rollout for low-latency trading)
├─ Monitor for 10 minutes
│   ├─ Order throughput: 1.1M orders/sec ✓
│   ├─ Latency p99: 4.2 μs ✓
│   └─ Error rate: 0% ✓
└─ Destroy Blue environment (old version)
        │
        ▼
✅ C++ Blue-Green Deployment Complete
Duration: 40 minutes (build + test) + 15 minutes (blue-green) = 55 minutes
Binary: 12 MB stripped C++ executable
Container: 33 MB (distroless base + binary)
Performance: 2.3 μs p50 latency, 1.2M orders/sec throughput
```

---

### Flow 4: C++ Bazel Monorepo (Google-style Build)

```
PM Command: "Deploy search-indexer v4.2 to production with canary"
        │
        ▼
Detection Results:
├─ Language: C++20
├─ Build Tool: Bazel 7.0
├─ Repository: Monorepo (12 services, 456 targets)
├─ Compiler: Clang 16
├─ Dependencies: Managed by Bazel (hermetic builds)
└─ Build Cache: Remote (Google Cloud Storage)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Jenkins Pipeline: PromptOps-CPP-Bazel-Canary-Deploy             │
└─────────────────────────────────────────────────────────────────┘

Stage 1: Bazel Build (Incremental + Cached) (3 minutes)
├─ Configure remote cache
│   └─ Command: bazel --remote_cache=grpc://cache.company.com:9090
├─ Build search-indexer target
│   └─ Command: bazel build //services/search:indexer \
│         --config=release \
│         --cxxopt='-std=c++20' \
│         --cxxopt='-O3' \
│         --cxxopt='-march=haswell'
│       ├─ Total targets: 456
│       ├─ Cached targets: 432 (94.7% cache hit rate!)
│       ├─ Rebuilt targets: 24 (only changed files)
│       ├─ Linking: bazel-bin/services/search/indexer
│       └─ Duration: 2m 45s (vs 45 min cold build)
│
└─ Bazel advantages for large C++ projects:
    ├─ Hermetic builds (reproducible)
    ├─ Incremental compilation (only rebuild changed targets)
    ├─ Remote caching (team-wide cache sharing)
    └─ Dependency graph analysis (what to rebuild)
        │
        ▼
Stage 2: Bazel Test (Parallel + Cached) (2 minutes)
├─ Run all tests for search-indexer
│   └─ Command: bazel test //services/search:all \
│         --test_output=errors \
│         --jobs=32
│       ├─ Test targets: 234
│       ├─ Cached test results: 198 (84.6% cache hit!)
│       ├─ Re-run tests: 36 (tests for changed code)
│       ├─ Passed: 234
│       ├─ Failed: 0
│       └─ Duration: 1m 50s (vs 25 min cold test run)
│
└─ Coverage report
    └─ Command: bazel coverage //services/search:all
        ├─ Coverage: 91.2%
        └─ Report: bazel-testlogs/coverage.dat
        │
        ▼
Stage 3-6: Standard deployment flow (same as CMake)
├─ Container build (33 MB distroless)
├─ Security scan
├─ Canary deployment (5% → 25% → 50% → 100%)
└─ Complete
        │
        ▼
✅ Bazel C++ Deployment Complete
Duration: 8 minutes (build + test) + 90 minutes (canary) = 98 minutes
Advantage: 80%+ cache hit rate = 5x faster builds!
```

---

## Build Pipeline Comparison

### Comparison Matrix: Java vs C++

| Feature | Java (Maven) | Java (Gradle) | C++ (CMake) | C++ (Bazel) |
|---------|-------------|---------------|-------------|-------------|
| **Build Time (Cold)** | 12 min | 8 min | 45 min | 45 min |
| **Build Time (Incremental)** | 5 min | 2 min | 8 min | 3 min |
| **Cache Hit Rate** | 60-70% | 70-80% | 50-60% | 85-95% |
| **Dependency Management** | Maven Central | Maven/Gradle repos | Conan/vcpkg | Bazel deps |
| **Build Parallelism** | ✓ (multi-module) | ✓✓ (better) | ✓✓ (make -j) | ✓✓✓ (best) |
| **Hermetic Builds** | ❌ (JVM version matters) | ❌ | ❌ | ✅ (fully) |
| **Container Image Size** | 255 MB (JRE + JAR) | 255 MB | 33 MB (distroless) | 33 MB |
| **Startup Time** | 3-5 seconds | 3-5 seconds | <100 ms | <100 ms |
| **Memory Footprint** | 512 MB (JVM heap) | 512 MB | 128 MB | 128 MB |
| **Latency (p99)** | 50-200 ms | 50-200 ms | 2-10 μs | 2-10 μs |
| **Throughput** | 10k req/sec | 10k req/sec | 1M+ req/sec | 1M+ req/sec |
| **Hot Reload** | ✅ Spring DevTools | ✅ | ❌ (recompile) | ❌ |
| **Ecosystem Maturity** | ✅✅✅ (huge) | ✅✅✅ | ✅✅ (good) | ✅ (growing) |

---

## Mixed-Language Applications

### Flow 5: Java Frontend + C++ Backend (Microservice Architecture)

```
Application: Real-time Analytics Platform
├─ Frontend API: Java Spring Boot (user-facing REST API)
├─ Processing Engine: C++ (low-latency data processing)
└─ Communication: gRPC (Java ↔ C++)

PM Command: "Deploy analytics-platform v2.0 to production with canary"
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│ Multi-Language Build Pipeline                                    │
└─────────────────────────────────────────────────────────────────┘

Parallel Build (Jenkins Pipeline)
        │
        ├───────────────────┬───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Java Frontend │   │ C++ Backend   │   │ Protobuf      │
│ (Maven)       │   │ (CMake)       │   │ (Shared)      │
│               │   │               │   │               │
│ 12 min        │   │ 45 min        │   │ 2 min         │
└───────┬───────┘   └───────┬───────┘   └───────┬───────┘
        │                   │                   │
        │                   │ Depends on        │
        │                   │ (gRPC service     │
        │                   │  definitions)     │
        └───────────────────┴───────────────────┘
                            │
                            ▼
            ┌───────────────────────────┐
            │ Build 2 Docker Images:    │
            │ 1. analytics-api:2.0      │
            │    (Java, 255 MB)         │
            │ 2. analytics-engine:2.0   │
            │    (C++, 33 MB)           │
            └───────────┬───────────────┘
                        │
                        ▼
            ┌───────────────────────────┐
            │ Deploy Both Services      │
            │ (Canary, synchronized)    │
            │                           │
            │ 5% canary:                │
            │ ├─ api:2.0 (5%)           │
            │ └─ engine:2.0 (5%)        │
            │                           │
            │ Monitor both services     │
            │ together                  │
            └───────────────────────────┘

✅ Multi-language deployment complete
Both services deployed in sync
Total duration: 45 min (parallel build) + 90 min (canary) = 135 min
```

---

## Performance Optimizations

### Java Performance Tuning

```dockerfile
# Dockerfile: Optimized Java Container

FROM eclipse-temurin:17-jre-alpine

# JVM tuning for containers
ENV JAVA_OPTS="\
    -XX:+UseContainerSupport \
    -XX:MaxRAMPercentage=75.0 \
    -XX:InitialRAMPercentage=50.0 \
    -XX:+UseG1GC \
    -XX:MaxGCPauseMillis=200 \
    -XX:+ParallelRefProcEnabled \
    -XX:+UseStringDeduplication \
    -XX:+AlwaysPreTouch \
    -XX:+OptimizeStringConcat \
    -Djava.security.egd=file:/dev/./urandom \
    -Dspring.backgroundpreinitializer.ignore=true"

# Application Performance Monitoring (APM)
ENV JAVA_OPTS="${JAVA_OPTS} \
    -javaagent:/app/dd-java-agent.jar \
    -Ddd.service=payment-processor \
    -Ddd.profiling.enabled=true"

COPY target/app.jar /app/app.jar
COPY dd-java-agent.jar /app/

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]
```

### C++ Performance Tuning

```dockerfile
# Dockerfile: Optimized C++ Container

FROM gcr.io/distroless/cc-debian11

# Binary compiled with maximum optimization
# Compilation flags used:
#   -O3                      (aggressive optimization)
#   -march=haswell           (target CPU architecture)
#   -flto                    (link-time optimization)
#   -ffast-math              (faster floating-point math)
#   -funroll-loops           (loop unrolling)
#   -finline-functions       (aggressive inlining)
#   -DNDEBUG                 (disable assertions)

COPY build/trading-engine /app/trading-engine

# CPU affinity (pin to specific cores)
ENV TRADING_ENGINE_CPU_AFFINITY="0-7"

# Huge pages (reduce TLB misses)
ENV TRADING_ENGINE_HUGE_PAGES="enabled"

# No ENTRYPOINT options needed - binary is pre-optimized
ENTRYPOINT ["/app/trading-engine"]
```

---

## Summary: Language-Specific Deployment Matrix

| Language | Build Tool | Build Time | Image Size | Startup | Use Case |
|----------|-----------|-----------|-----------|---------|----------|
| **Java** | Maven | 12 min | 255 MB | 3-5s | Business logic, CRUD APIs |
| **Java** | Gradle | 8 min | 255 MB | 3-5s | Microservices, Kotlin apps |
| **C++** | CMake | 45 min (3 min incr) | 33 MB | <100ms | Low-latency, high-throughput |
| **C++** | Bazel | 45 min (3 min incr) | 33 MB | <100ms | Large monorepos |
| **Java+C++** | Mixed | 45 min (parallel) | Both | Both | Hybrid architectures |

---

**PromptOps — Java & C++ Deployment Flows — Version 1.0 — May 2026**  
*Complete guide for deploying compiled language applications through PromptOps*

**Confidential — Internal Engineering Document**
