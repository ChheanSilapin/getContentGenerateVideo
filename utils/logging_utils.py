"""
Logging utilities for controlling verbose output in the video generator
"""
import config

def should_log(category: str) -> bool:
    """
    Check if a specific logging category should be displayed
    
    Args:
        category: Logging category (e.g., 'performance_status', 'speech_recognition')
    
    Returns:
        bool: True if logging is enabled for this category
    """
    try:
        logging_config = getattr(config, 'LOGGING_CONFIG', {})
        
        # If verbose mode is enabled, show everything
        if logging_config.get('verbose_mode', False):
            return True
            
        # Check specific category
        return logging_config.get(f'show_{category}', False)
    except Exception:
        # Default to showing logs if config is unavailable
        return True

def log_if_enabled(category: str, message: str, force: bool = False):
    """
    Print a log message only if the category is enabled
    
    Args:
        category: Logging category
        message: Message to log
        force: Force logging regardless of settings (for critical messages)
    """
    if force or should_log(category):
        print(message)

def clean_log_message(message: str, remove_emojis: bool = None) -> str:
    """
    Clean up log messages by removing emojis if configured
    
    Args:
        message: Original message
        remove_emojis: Override emoji removal setting
    
    Returns:
        str: Cleaned message
    """
    try:
        logging_config = getattr(config, 'LOGGING_CONFIG', {})
        
        if remove_emojis is None:
            remove_emojis = not logging_config.get('show_emojis', False)
        
        if remove_emojis:
            # Remove common emojis used in the application
            emoji_replacements = {
                '🚀': '[PERF]',
                '✅': '[OK]',
                '❌': '[ERROR]',
                '⚠️': '[WARN]',
                '📝': '[PROC]',
                '🎯': '[APPLY]',
                '💾': '[CACHE]',
                '🧹': '[CLEAN]',
                '🔄': '[RETRY]',
            }
            
            for emoji, replacement in emoji_replacements.items():
                message = message.replace(emoji, replacement)
        
        return message
    except Exception:
        return message

def log_performance_status(message: str):
    """Log performance-related messages"""
    cleaned_message = clean_log_message(message)
    log_if_enabled('performance_status', cleaned_message)

def log_content_analysis(message: str):
    """Log content analysis messages"""
    cleaned_message = clean_log_message(message)
    log_if_enabled('content_analysis', cleaned_message)

def log_speech_recognition(message: str):
    """Log speech recognition messages"""
    cleaned_message = clean_log_message(message)
    log_if_enabled('speech_recognition', cleaned_message)

def log_file_operations(message: str):
    """Log file operation messages"""
    cleaned_message = clean_log_message(message)
    log_if_enabled('file_operations', cleaned_message)

def log_cache_operations(message: str):
    """Log cache operation messages"""
    cleaned_message = clean_log_message(message)
    log_if_enabled('cache_operations', cleaned_message)

def log_ffmpeg_commands(message: str):
    """Log FFmpeg command messages"""
    cleaned_message = clean_log_message(message)
    log_if_enabled('ffmpeg_commands', cleaned_message)

def log_essential(message: str):
    """Log essential messages that should always be shown"""
    cleaned_message = clean_log_message(message)
    print(cleaned_message)

def log_step(step_number: int, total_steps: int, description: str):
    """Log processing steps in a clean format"""
    message = f"[{step_number}/{total_steps}] {description}"
    log_essential(message)
