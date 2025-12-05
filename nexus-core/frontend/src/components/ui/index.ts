/**
 * UI Components Index
 *
 * Central export for all child-friendly UI components.
 * These components are designed with EAL students in mind:
 * - Large touch targets
 * - Visual feedback over text
 * - Playful animations
 * - Accessible by default
 */

// Core UI Components
export { VisualButton, type VisualButtonProps } from './VisualButton';
export { AnimatedCharacter, type AnimatedCharacterProps, type CharacterMood } from './AnimatedCharacter';
export { ProgressIndicator, type ProgressIndicatorProps } from './ProgressIndicator';
export { VisualFeedback, type VisualFeedbackProps, type FeedbackType } from './VisualFeedback';
export { LoadingSpinner, type LoadingSpinnerProps, type SpinnerVariant } from './LoadingSpinner';

// Audio Components
export {
    AudioPlayer,
    useAudioFeedback,
    type AudioPlayerProps,
    type AudioPlayerHandle,
    type SoundType,
} from './AudioPlayer';

// PWA Components
export { OfflineIndicator, OfflineDot, type OfflineIndicatorProps } from './OfflineIndicator';
