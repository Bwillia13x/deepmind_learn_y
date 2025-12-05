# NEXUS Audio Feedback System

This folder is reserved for optional audio files. However, NEXUS uses **Web Audio API** to generate sounds programmatically, so no external audio files are required.

## Sound Generation

All UI sounds are generated in real-time using the Web Audio API in `/src/components/ui/AudioPlayer.tsx`. This approach:

1. **Reduces bundle size** - No audio files to download
2. **Works offline** - Sounds work without network
3. **Is customizable** - Frequencies and durations are easily adjustable
4. **Is accessible** - Can be enabled/disabled per user preference

## Available Sound Types

| Sound Type | Description | Use Case |
|------------|-------------|----------|
| `success` | Happy ascending melody (C5→E5→G5) | Correct answer, task complete |
| `error` | Low descending tone (D#4→C4) | Incorrect attempt, validation error |
| `click` | Short click (800Hz) | Button press feedback |
| `complete` | Victory fanfare melody | Session complete, achievement |
| `start` | Ready tone (A4→C#5) | Session start, ready state |
| `celebration` | Flourish melody | Big achievements, milestones |

## Usage in Components

```tsx
import { useAudioFeedback } from '@/components/ui/AudioPlayer';

function MyComponent() {
  const { play } = useAudioFeedback();
  
  const handleSuccess = () => {
    play('success');
  };
  
  return <button onClick={handleSuccess}>Click me!</button>;
}
```

## Custom Audio Files (Optional)

If you want to add custom audio files for branding or specific sounds:

1. Add `.mp3` or `.ogg` files to this folder
2. Update `AudioPlayer.tsx` to load files instead of generating tones
3. Consider file size impact on initial load

## Accessibility Notes

- Audio feedback is **disabled by default** for users with `prefers-reduced-motion`
- Volume can be adjusted via the `useAudioFeedback` hook
- Audio can be globally disabled in user preferences
- All audio feedback is supplemental (never required for functionality)
