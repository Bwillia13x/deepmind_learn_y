# NEXUS Design System

This document outlines the design system used in the NEXUS application.

## Colors

### Brand Colors

- **Primary (Blue)**: `#2563eb` (Tailwind: `nexus-primary`) - Used for main actions, active states, and branding.
- **Secondary (Purple)**: `#7c3aed` (Tailwind: `nexus-secondary`) - Used for accents, gradients, and "magic" effects.
- **Accent (Cyan)**: `#06b6d4` (Tailwind: `nexus-accent`) - Used for highlights and special indicators.
- **Success (Green)**: `#10b981` (Tailwind: `nexus-success`) - Used for positive feedback and completion states.
- **Warning (Amber)**: `#f59e0b` (Tailwind: `nexus-warning`) - Used for alerts and attention-grabbing elements.
- **Error (Red)**: `#ef4444` (Tailwind: `nexus-error`) - Used for error states and destructive actions.

### Semantic Colors

- **Background**: `hsl(var(--background))` - Main background color.
- **Foreground**: `hsl(var(--foreground))` - Main text color.
- **Card**: `hsl(var(--card))` - Card background color.
- **Muted**: `hsl(var(--muted))` - Muted background/text color.

## Typography

- **Font**: Inter (via `next/font/google`)
- **Headings**: Bold, tight tracking.
- **Body**: Regular, relaxed line height.

## UI Patterns

### Glassmorphism

Used for cards, panels, and overlays to create a modern, airy feel.

- Class: `.glass` or `.glass-card`
- Properties: `backdrop-blur-md`, `bg-white/70` (light), `bg-black/70` (dark), `border-white/20`.

### Gradients

Used for text and backgrounds to add depth.

- Text Gradient: `.text-gradient-primary` (`bg-gradient-to-r from-nexus-primary to-nexus-secondary`)
- Background Gradient: `bg-gradient-to-br from-nexus-primary/5 to-nexus-secondary/5`

### Animations

Custom animations defined in `tailwind.config.js`.

- `animate-float`: Gentle floating motion for characters and orbs.
- `animate-pulse-soft`: Soft opacity pulse for loading states.
- `animate-pulse-ring`: Expanding ring effect for listening states.
- `animate-speak-wave`: Vertical scaling for speaking states.
- `animate-fade-in`: Fade in effect for page transitions.
- `animate-slide-up`: Slide up effect for entering elements.

## Components

### Voice Orb

The central interaction point for the student.

- **Idle**: Floating, `nexus-primary`.
- **Listening**: Pulsing ring, `nexus-success`.
- **Processing**: Spinning, `nexus-secondary`.
- **Speaking**: Wave animation, `nexus-primary`.

### Animated Character

The friendly companion for the student.

- Uses SVG fills based on mood (`nexus-primary`, `nexus-secondary`, etc.).
- Subtle animations for engagement.

### Visual Feedback

- **Success**: Green checkmark, bounce animation.
- **Error**: Red X, shake animation.
- **Progress**: Colored bars/dots (`nexus-primary` -> `nexus-success`).
