/**
 * Tests for VisualButton Component
 *
 * Verifies child-friendly button interactions and accessibility.
 */

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { VisualButton } from "@/components/ui/VisualButton";
import { Mic, Play, Square } from "lucide-react";

describe("VisualButton", () => {
    describe("Rendering", () => {
        it("renders with icon and aria-label", () => {
            render(
                <VisualButton icon={<Mic data-testid="mic-icon" />} ariaLabel="Start recording" />
            );
            expect(screen.getByRole("button")).toBeInTheDocument();
            expect(screen.getByLabelText("Start recording")).toBeInTheDocument();
        });

        it("renders with optional label text", () => {
            render(
                <VisualButton
                    icon={<Play />}
                    label="Start"
                    ariaLabel="Start the session"
                />
            );
            expect(screen.getByText("Start")).toBeInTheDocument();
        });

        it("renders icon correctly", () => {
            render(
                <VisualButton
                    icon={<Mic data-testid="mic-icon" />}
                    ariaLabel="Microphone"
                />
            );
            expect(screen.getByTestId("mic-icon")).toBeInTheDocument();
        });
    });

    describe("Interactions", () => {
        it("calls onClick when clicked", () => {
            const handleClick = vi.fn();
            render(
                <VisualButton
                    icon={<Play />}
                    ariaLabel="Play"
                    onClick={handleClick}
                />
            );

            fireEvent.click(screen.getByRole("button"));
            expect(handleClick).toHaveBeenCalledTimes(1);
        });

        it("does not call onClick when disabled", () => {
            const handleClick = vi.fn();
            render(
                <VisualButton
                    icon={<Play />}
                    ariaLabel="Play"
                    onClick={handleClick}
                    disabled={true}
                />
            );

            fireEvent.click(screen.getByRole("button"));
            expect(handleClick).not.toHaveBeenCalled();
        });

        it("does not call onClick when loading", () => {
            const handleClick = vi.fn();
            render(
                <VisualButton
                    icon={<Play />}
                    ariaLabel="Play"
                    onClick={handleClick}
                    loading={true}
                />
            );

            fireEvent.click(screen.getByRole("button"));
            expect(handleClick).not.toHaveBeenCalled();
        });
    });

    describe("States", () => {
        it("applies disabled attribute when disabled", () => {
            render(
                <VisualButton icon={<Square />} ariaLabel="Stop" disabled={true} />
            );
            expect(screen.getByRole("button")).toBeDisabled();
        });

        it("applies aria-busy when loading", () => {
            render(
                <VisualButton icon={<Square />} ariaLabel="Stop" loading={true} />
            );
            expect(screen.getByRole("button")).toHaveAttribute("aria-busy", "true");
        });

        it("is disabled when loading", () => {
            render(
                <VisualButton icon={<Square />} ariaLabel="Stop" loading={true} />
            );
            expect(screen.getByRole("button")).toBeDisabled();
        });
    });

    describe("Variants", () => {
        it("applies primary variant classes by default", () => {
            render(<VisualButton icon={<Play />} ariaLabel="Play" />);
            const button = screen.getByRole("button");
            expect(button).toHaveClass("bg-primary");
        });

        it("applies secondary variant classes", () => {
            render(
                <VisualButton icon={<Play />} ariaLabel="Play" variant="secondary" />
            );
            const button = screen.getByRole("button");
            expect(button).toHaveClass("bg-secondary");
        });

        it("applies success variant classes", () => {
            render(
                <VisualButton icon={<Play />} ariaLabel="Play" variant="success" />
            );
            const button = screen.getByRole("button");
            expect(button).toHaveClass("bg-success");
        });

        it("applies ghost variant classes", () => {
            render(
                <VisualButton icon={<Play />} ariaLabel="Play" variant="ghost" />
            );
            const button = screen.getByRole("button");
            expect(button).toHaveClass("bg-muted");
        });
    });

    describe("Sizes", () => {
        it("applies small size classes", () => {
            render(<VisualButton icon={<Play />} ariaLabel="Play" size="sm" />);
            const button = screen.getByRole("button");
            expect(button).toHaveClass("w-16", "h-16");
        });

        it("applies medium size classes by default", () => {
            render(<VisualButton icon={<Play />} ariaLabel="Play" />);
            const button = screen.getByRole("button");
            expect(button).toHaveClass("w-20", "h-20");
        });

        it("applies large size classes", () => {
            render(<VisualButton icon={<Play />} ariaLabel="Play" size="lg" />);
            const button = screen.getByRole("button");
            expect(button).toHaveClass("w-28", "h-28");
        });

        it("applies extra-large size classes", () => {
            render(<VisualButton icon={<Play />} ariaLabel="Play" size="xl" />);
            const button = screen.getByRole("button");
            expect(button).toHaveClass("w-36", "h-36");
        });
    });

    describe("Accessibility", () => {
        it("has required aria-label", () => {
            render(<VisualButton icon={<Mic />} ariaLabel="Record voice" />);
            expect(screen.getByRole("button")).toHaveAttribute(
                "aria-label",
                "Record voice"
            );
        });

        it("has button type attribute", () => {
            render(<VisualButton icon={<Mic />} ariaLabel="Record" />);
            expect(screen.getByRole("button")).toHaveAttribute("type", "button");
        });

        it("supports keyboard interaction via focus", () => {
            render(<VisualButton icon={<Play />} ariaLabel="Play" />);
            const button = screen.getByRole("button");
            button.focus();
            expect(document.activeElement).toBe(button);
        });
    });

    describe("Custom className", () => {
        it("applies additional custom classes", () => {
            render(
                <VisualButton
                    icon={<Play />}
                    ariaLabel="Play"
                    className="my-custom-class"
                />
            );
            expect(screen.getByRole("button")).toHaveClass("my-custom-class");
        });
    });
});
