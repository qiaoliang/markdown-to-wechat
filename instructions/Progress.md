```mermaid
graph TD
    %% Existing Components
    CLI[cli.py]
    MD[md_file.py]
    HTML[wx_htmler.py]
    IMG[image_processor.py]
    CACHE[wx_cache.py]
    PUB[wx_publisher.py]
    WCLIENT[wx_client.py]

    %% Planned Components
    ERR[Error Handling System]
    HUGO[Hugo Format Support]
    ROUTER[OpenRouter Integration]
    IMG_ENH[Enhanced Image Management]

    %% Dependencies between existing components
    CLI --> MD
    CLI --> PUB
    MD --> IMG
    HTML --> MD
    PUB --> HTML
    PUB --> IMG
    PUB --> WCLIENT
    PUB --> CACHE
    IMG --> CACHE

    %% Dependencies for Error Handling System
    ERR --> CLI
    ERR --> MD
    ERR --> IMG
    ERR --> PUB
    ERR --> WCLIENT
    ERR --> ROUTER
    ERR --> IMG_ENH

    %% Dependencies for Hugo Support
    HUGO --> MD
    HUGO --> IMG_ENH
    HUGO --> ERR
    HUGO --> ROUTER

    %% Dependencies for OpenRouter Integration
    ROUTER --> MD
    ROUTER --> CACHE
    ROUTER --> ERR

    %% Dependencies for Enhanced Image Management
    IMG_ENH --> IMG
    IMG_ENH --> CACHE
    IMG_ENH --> ERR

    %% Styling
    classDef existing fill:#90EE90,stroke:#006400,color:#0000FF
    classDef planned fill:#FFB6C1,stroke:#8B0000,color:#0000FF
    
    %% Apply styles
    class CLI,MD,HTML,IMG,CACHE,PUB,WCLIENT existing
    class ERR,HUGO,ROUTER,IMG_ENH planned

    %% Subgraphs for organization
    subgraph Existing Components
        CLI
        MD
        HTML
        IMG
        CACHE
        PUB
        WCLIENT
    end

    subgraph Planned Components
        ERR
        HUGO
        ROUTER
        IMG_ENH
    end

    %% Style for subgraph titles
    style Existing Components fill:#fff,stroke:#000,color:#0000FF
    style Planned Components fill:#fff,stroke:#000,color:#0000FF