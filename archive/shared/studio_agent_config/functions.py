"""
Configuration Functions for Mistral AI Studio Agent

This module provides functions to update various aspects of the
Mistral AI Studio Agent configuration.
"""

from typing import Dict, Optional

from .models import (
    MistralStudioAgentConfig,
    LightingConfig,
    WeatherConfig,
    BackgroundMusicConfig,
    AmbientSoundsConfig,
    SeatingConfig,
    SoundConfig,
    AmbianceConfig,
    ApiConfiguration,
    ApiEndpointConfig,
    AuthenticationConfig,
    ModelParameters,
    ModelConfig,
    GridMistralAgentConfig,
    PurposeConfig,
    CommunicationGuidelines,
    TaskExecutionConfig,
    TaskConstraints,
    ErrorHandlingConfig,
    UnavailableServicesConfig,
    ConfidenceThresholdsConfig,
    ValidationIssuesConfig,
    OutputFormattingConfig,
    ConstraintsAndComplianceConfig,
    UserInteractionConfig,
    TaskExample,
    ExamplesConfig,
    LimiterPluginConfig,
    SystemPromptConfig,
)


def set_lighting(
    config: MistralStudioAgentConfig,
    type: str,
    intensity: str,
    color_temperature: int,
) -> MistralStudioAgentConfig:
    """
    Update lighting configuration.

    Args:
        config: Current configuration instance
        type: Lighting type (warm/cool/neutral)
        intensity: Lighting intensity (low/moderate/high)
        color_temperature: Color temperature in Kelvin (2000-6500K)

    Returns:
        Updated configuration instance
    """
    new_lighting = LightingConfig(
        type=type, intensity=intensity, color_temperature=color_temperature
    )
    config.ambiance.lighting = new_lighting
    return config


def set_weather(
    config: MistralStudioAgentConfig,
    condition: str,
    intensity: str,
    acceleration_pattern: str,
) -> MistralStudioAgentConfig:
    """
    Update weather configuration.

    Args:
        config: Current configuration instance
        condition: Weather condition (rain/sunny/cloudy/storm)
        intensity: Weather intensity (light/moderate/moody/heavy)
        acceleration_pattern: Acceleration pattern (breathing/steady/pulsing/random)

    Returns:
        Updated configuration instance
    """
    new_weather = WeatherConfig(
        condition=condition, intensity=intensity, acceleration_pattern=acceleration_pattern
    )
    config.ambiance.weather = new_weather
    return config


def set_background_music(
    config: MistralStudioAgentConfig,
    genre: str,
    playlist: str,
    current_track: str,
) -> MistralStudioAgentConfig:
    """
    Update background music configuration.

    Args:
        config: Current configuration instance
        genre: Music genre
        playlist: Playlist name or identifier
        current_track: Current track identifier or name

    Returns:
        Updated configuration instance
    """
    new_music = BackgroundMusicConfig(
        genre=genre, playlist=playlist, current_track=current_track
    )
    config.ambiance.sound.background_music = new_music
    return config


def set_ambient_sounds(
    config: MistralStudioAgentConfig,
    rain: str,
    coffee_shop: str,
) -> MistralStudioAgentConfig:
    """
    Update ambient sounds configuration.

    Args:
        config: Current configuration instance
        rain: Rain sound intensity (low/moderate/moderately_busy/busy)
        coffee_shop: Coffee shop ambient sound intensity

    Returns:
        Updated configuration instance
    """
    new_ambient = AmbientSoundsConfig(rain=rain, coffee_shop=coffee_shop)
    config.ambiance.sound.ambient_sounds = new_ambient
    return config


def set_seating(
    config: MistralStudioAgentConfig,
    location: str,
    reason: str,
) -> MistralStudioAgentConfig:
    """
    Update seating configuration.

    Args:
        config: Current configuration instance
        location: Seating location (e.g., 'balcony/roadside')
        reason: Reason for seating choice (e.g., 'small_indoor_space')

    Returns:
        Updated configuration instance
    """
    new_seating = SeatingConfig(location=location, reason=reason)
    config.ambiance.seating = new_seating
    return config


def set_api_configuration(
    config: MistralStudioAgentConfig,
    base_url: str,
    endpoints: Dict[str, str],
    authentication: Dict[str, str],
) -> MistralStudioAgentConfig:
    """
    Update API configuration.

    Args:
        config: Current configuration instance
        base_url: Base URL for the API
        endpoints: Dictionary with 'chat' and 'models' endpoint paths
        authentication: Dictionary with 'type' and 'env_var' for authentication

    Returns:
        Updated configuration instance
    """
    endpoint_config = ApiEndpointConfig(
        chat=endpoints.get("chat", "/chat/completions"),
        models=endpoints.get("models", "/models"),
    )
    auth_config = AuthenticationConfig(
        type=authentication.get("type", "api_key"),
        env_var=authentication.get("env_var", "MISTRAL_API_KEY"),
    )
    new_api_config = ApiConfiguration(
        base_url=base_url, endpoints=endpoint_config, authentication=auth_config
    )
    config.api_configuration = new_api_config
    return config


def set_model_parameters(
    config: MistralStudioAgentConfig,
    model_id: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    frequency_penalty: Optional[float] = None,
    presence_penalty: Optional[float] = None,
) -> MistralStudioAgentConfig:
    """
    Update model parameters for a specific model.

    Args:
        config: Current configuration instance
        model_id: Model identifier (e.g., 'codestral', 'pixtral')
        temperature: Sampling temperature (0.0-2.0)
        max_tokens: Maximum number of tokens to generate
        top_p: Nucleus sampling parameter (0.0-1.0)
        frequency_penalty: Frequency penalty (-2.0 to 2.0)
        presence_penalty: Presence penalty (-2.0 to 2.0)

    Returns:
        Updated configuration instance

    Raises:
        ValueError: If model_id is not found in configuration
    """
    if model_id not in config.models:
        raise ValueError(f"Model '{model_id}' not found in configuration")

    model_config = config.models[model_id]
    current_params = model_config.parameters

    new_params = ModelParameters(
        temperature=temperature if temperature is not None else current_params.temperature,
        max_tokens=max_tokens if max_tokens is not None else current_params.max_tokens,
        top_p=top_p if top_p is not None else current_params.top_p,
        frequency_penalty=(
            frequency_penalty
            if frequency_penalty is not None
            else current_params.frequency_penalty
        ),
        presence_penalty=(
            presence_penalty
            if presence_penalty is not None
            else current_params.presence_penalty
        ),
    )

    model_config.parameters = new_params
    return config


def load_config(file_path: str) -> MistralStudioAgentConfig:
    """
    Load configuration from JSON file.

    Args:
        file_path: Path to JSON configuration file

    Returns:
        Loaded and validated configuration instance
    """
    return MistralStudioAgentConfig.from_json_file(file_path)


def save_config(config: MistralStudioAgentConfig, file_path: str) -> None:
    """
    Save configuration to JSON file.

    Args:
        config: Configuration instance to save
        file_path: Path to save JSON configuration file
    """
    config.to_json_file(file_path)


def get_default_config() -> MistralStudioAgentConfig:
    """
    Get default configuration based on the provided schema.

    Returns:
        Default configuration instance with all settings initialized
    """
    return MistralStudioAgentConfig(
        studio_name="Moody Rainy Coffee Shop",
        agent_name="MistralAIIntegrationAgent",
        description="An agent that integrates Mistral AI models locally through the API in a moody rainy coffee shop ambiance.",
        ambiance=AmbianceConfig(
            lighting=LightingConfig(
                type="warm", intensity="moderate", color_temperature=2700
            ),
            weather=WeatherConfig(
                condition="rain", intensity="moody", acceleration_pattern="breathing"
            ),
            sound=SoundConfig(
                background_music=BackgroundMusicConfig(
                    genre="jazz_and_blues",
                    playlist="moody_evening",
                    current_track="eric_clapton_wonderful_night",
                ),
                ambient_sounds=AmbientSoundsConfig(
                    rain="moderate", coffee_shop="moderately_busy"
                ),
            ),
            seating=SeatingConfig(
                location="balcony/roadside", reason="small_indoor_space"
            ),
        ),
        api_configuration=ApiConfiguration(
            base_url="https://api.mistral.ai/v1",
            endpoints=ApiEndpointConfig(
                chat="/chat/completions", models="/models"
            ),
            authentication=AuthenticationConfig(
                type="api_key", env_var="MISTRAL_API_KEY"
            ),
        ),
        models={
            "codestral": ModelConfig(
                model_id="codestral",
                parameters=ModelParameters(
                    temperature=0.7,
                    max_tokens=100,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                ),
            ),
            "pixtral": ModelConfig(
                model_id="pixtral",
                parameters=ModelParameters(
                    temperature=0.7,
                    max_tokens=100,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                ),
            ),
            "mistral": ModelConfig(
                model_id="mistral",
                parameters=ModelParameters(
                    temperature=0.7,
                    max_tokens=100,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                ),
            ),
            "ministral": ModelConfig(
                model_id="ministral",
                parameters=ModelParameters(
                    temperature=0.7,
                    max_tokens=100,
                    top_p=1.0,
                    frequency_penalty=0.0,
                    presence_penalty=0.0,
                ),
            ),
        },
        environment_variables={
            "MISTRAL_API_KEY": "your_api_key_here",
            "MISTRAL_API_BASE_URL": "https://api.mistral.ai/v1",
        },
    )


# GRID Agent Functions


def validate_confidence_threshold(threshold: float) -> bool:
    """
    Validate confidence threshold value.

    Args:
        threshold: Confidence threshold value (0.0-1.0)

    Returns:
        True if threshold is valid

    Raises:
        ValueError: If threshold is outside valid range
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("Confidence threshold must be between 0.0 and 1.0")
    return True


def get_task_execution_config(
    config: GridMistralAgentConfig, task_type: str
) -> TaskExecutionConfig:
    """
    Get task execution configuration for a specific task type.

    Args:
        config: GRID agent configuration instance
        task_type: Task type (pattern_recognition, data_validation, decision_logging, artifact_generation, capability_retrieval)

    Returns:
        Task execution configuration for the specified task type

    Raises:
        ValueError: If task_type is not found in configuration
    """
    if task_type not in config.task_execution:
        raise ValueError(
            f"Task type '{task_type}' not found in configuration. "
            f"Available types: {list(config.task_execution.keys())}"
        )
    return config.task_execution[task_type]


def get_error_handling_config(
    config: GridMistralAgentConfig, error_type: str
) -> UnavailableServicesConfig | ConfidenceThresholdsConfig | ValidationIssuesConfig:
    """
    Get error handling configuration for a specific error type.

    Args:
        config: GRID agent configuration instance
        error_type: Error type (unavailable_services, confidence_thresholds, validation_issues)

    Returns:
        Error handling configuration for the specified error type

    Raises:
        ValueError: If error_type is not found in configuration
    """
    error_config_map = {
        "unavailable_services": config.error_handling.unavailable_services,
        "confidence_thresholds": config.error_handling.confidence_thresholds,
        "validation_issues": config.error_handling.validation_issues,
    }

    if error_type not in error_config_map:
        raise ValueError(
            f"Error type '{error_type}' not found in configuration. "
            f"Available types: {list(error_config_map.keys())}"
        )
    return error_config_map[error_type]


def validate_agent_config(config: GridMistralAgentConfig) -> bool:
    """
    Validate GRID agent configuration against requirements.

    Args:
        config: GRID agent configuration instance

    Returns:
        True if configuration is valid

    Raises:
        ValueError: If configuration validation fails
    """
    # Validate required task execution types
    required_task_types = [
        "pattern_recognition",
        "data_validation",
        "decision_logging",
        "artifact_generation",
        "capability_retrieval",
    ]

    for task_type in required_task_types:
        if task_type not in config.task_execution:
            raise ValueError(
                f"Required task type '{task_type}' missing from task_execution configuration"
            )

    # Validate that all descriptions are non-empty (handled by Pydantic)
    # Additional custom validation can be added here

    return True


def get_grid_agent_default_config() -> GridMistralAgentConfig:
    """
    Get default GRID agent configuration based on the provided schema.

    Returns:
        Default GRID agent configuration instance with all settings initialized
    """
    return GridMistralAgentConfig(
        agent_name="MistralAgent",
        description="An agent designed to assist with pattern recognition, data validation, decision logging, artifact generation, and dynamic capability retrieval within the GRID ecosystem.",
        purpose=PurposeConfig(
            pattern_recognition="Identify and extract relevant entities, relationships, sentiment, and intent from input text.",
            data_validation="Validate discussion rows against the Great Hall decision table schema.",
            decision_logging="Record decisions and their supporting context accurately and comprehensively.",
            artifact_generation="Generate artifacts in the specified format (JSON, markdown, HTML, CSV).",
            capability_retrieval="Dynamically retrieve and initialize GRID subsystems or tools based on context.",
        ),
        communication_guidelines=CommunicationGuidelines(
            clarity_and_conciseness="Provide clear, concise, and actionable responses. Avoid jargon unless it is specific to the GRID ecosystem and necessary for the task.",
            context_awareness="Always consider the context of the conversation and the specific task at hand. Use context to inform responses and actions.",
            user_centric_approach="Prioritize the user's needs and preferences. Tailor responses to the user's level of expertise and familiarity with the GRID ecosystem.",
        ),
        task_execution={
            "pattern_recognition": TaskExecutionConfig(
                description="Extract relevant entities, relationships, sentiment, and intent from input text.",
                constraints=TaskConstraints(
                    context_window="Specified context window",
                    confidence_thresholds="Specified confidence thresholds",
                ),
            ),
            "data_validation": TaskExecutionConfig(
                description="Validate discussion rows against the Great Hall decision table schema.",
                feedback="Provide clear feedback on any issues or suggested fixes.",
            ),
            "decision_logging": TaskExecutionConfig(
                description="Record decisions and their supporting context accurately and comprehensively.",
                traceability="Ensure that all decisions are traceable and conform to the Great Hall schema.",
            ),
            "artifact_generation": TaskExecutionConfig(
                description="Generate artifacts in the specified format (JSON, markdown, HTML, CSV).",
                validation="Validate artifacts against the relevant schema to ensure compliance and accuracy.",
            ),
            "capability_retrieval": TaskExecutionConfig(
                description="Dynamically retrieve and initialize GRID subsystems or tools based on context.",
                warnings="Provide clear instructions or warnings if a capability is unavailable or requires additional setup.",
            ),
        },
        error_handling=ErrorHandlingConfig(
            unavailable_services=UnavailableServicesConfig(
                description="If a required service (e.g., NER service) is unavailable, provide a fallback response or basic lexical pattern matches.",
                communication="Clearly communicate any limitations or issues to the user.",
            ),
            confidence_thresholds=ConfidenceThresholdsConfig(
                description="Mark outputs as 'uncertain' if confidence levels are below the specified threshold.",
                recommendations="Provide recommendations for improving confidence levels if applicable.",
            ),
            validation_issues=ValidationIssuesConfig(
                description="Clearly indicate any validation issues and provide suggested fixes.",
                actionability="Ensure that validation results are easily understandable and actionable.",
            ),
        ),
        output_formatting=OutputFormattingConfig(
            consistency="Maintain consistent formatting for outputs, including timestamps, IDs, and metadata. Use ISO 8601 format for all timestamps.",
            readability="Ensure that outputs are readable and self-contained, especially for markdown and HTML formats. Include headers and proper escaping for CSV outputs.",
            provenance="Include provenance information (source lines/references) where applicable. Ensure that all outputs are traceable and reproducible.",
        ),
        constraints_and_compliance=ConstraintsAndComplianceConfig(
            adherence_to_schema="Ensure that all generated artifacts comply with the relevant schema (e.g., OPEN_POLICY.md contract). Validate schema versions and required fields for all artifacts.",
            constraints="Adhere to specified constraints such as maximum analysis window, entity confidence thresholds, and relationship depth. Ensure that all outputs meet the specified constraints (e.g., content length, explicit timelines).",
            compliance="Ensure that all actions and outputs comply with the GRID ecosystem's policies and guidelines. Cross-reference linked criteria and options against the session schema.",
        ),
        user_interaction=UserInteractionConfig(
            feedback="Provide clear and constructive feedback on user inputs. Offer suggestions for improvement or correction when necessary.",
            transparency="Be transparent about the agent's capabilities and limitations. Clearly communicate any assumptions or inferences made during task execution.",
            responsiveness="Respond promptly to user queries and requests. Keep the user informed about the progress and status of tasks.",
        ),
        examples=ExamplesConfig(
            pattern_recognition=TaskExample(
                description="Extract entities, relationships, sentiment, and intent from input text.",
                example="For input text, extract entities, relationships, sentiment, and intent, and mark evidence references and citations. Example: 'Alice proposed a 3-month trial of the new scheduling system. Bob raised concerns about data privacy.'",
            ),
            data_validation=TaskExample(
                description="Validate a discussion row and provide feedback on its conformity to the Great Hall schema.",
                example="Validate a bridge proposal with linked criteria and options.",
            ),
            decision_logging=TaskExample(
                description="Record a decision with its rationale, affected criteria, owner, timeline, and success metrics.",
                example="Log a decision to implement a gradual rollout with a 2-week pilot.",
            ),
            artifact_generation=TaskExample(
                description="Generate a Great Hall record with meta, session, discussion rows, decisions, and action items.",
                example="Create a JSON artifact for a Q1 planning session.",
            ),
            capability_retrieval=TaskExample(
                description="Retrieve and initialize a GRID capability, such as the NER service or Codestral client.",
                example="Retrieve the NER service and provide its methods and configuration.",
            ),
        ),
        limiter_plugin=LimiterPluginConfig(
            word_counter="Counts the number of words in each sentence/paragraph.",
            summarizer="If the word count exceeds the threshold, it activates a summarization function to condense the text.",
            warning_message_generator="Displays a warning message if the summarization function is triggered.",
        ),
        system_prompt_summarization=SystemPromptConfig(
            original_system_prompt="General Instructions for Mistral Agent in GRID Ecosystem",
            summarized_system_prompt="The Mistral agent assists with pattern recognition, data validation, decision logging, artifact generation, and dynamic capability retrieval within the GRID ecosystem. Key guidelines include: Communication: Be clear, concise, context-aware, user-centric, and avoid unnecessary jargon. Task Execution: Pattern Recognition: Extract relevant entities, relationships, sentiment, and intent from input text. Data Validation: Validate discussion rows against the Great Hall schema; provide clear feedback on issues. Decision Logging: Record decisions accurately with context, traceability, and compliance to Great Hall schema. Artifact Generation: Generate artifacts in specified formats (JSON, markdown, HTML, CSV); validate against relevant schemas. Capability Retrieval: Dynamically retrieve GRID subsystems or tools based on context; warn users of unavailable capabilities. Error Handling: Address unavailable services with fallback responses; mark uncertain outputs and provide recommendations for improving confidence levels. Output Formatting: Maintain consistent formatting, readability, and traceability in outputs. Include provenance information where applicable. Constraints & Compliance: Ensure adherence to schemas, specified constraints, GRID ecosystem policies, and cross-reference linked criteria against session schema. User Interaction: Provide clear feedback, transparency about capabilities/limitations, prompt responsiveness, and inform users about task progress/status.",
            warning_message="Warning: Text exceeds the defined threshold. It has been summarized for clarity.",
        ),
    )
