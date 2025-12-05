/**
 * Tests for LoadingSpinner Component
 *
 * Verifies child-friendly loading indicators render correctly.
 */

import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";

describe("LoadingSpinner", () => {
    describe("Rendering", () => {
        it("renders with default props", () => {
            render(<LoadingSpinner />);
            expect(screen.getByRole("status")).toBeInTheDocument();
        });

        it("renders with custom aria-label", () => {
            render(<LoadingSpinner ariaLabel="Loading your session" />);
            expect(screen.getByLabelText("Loading your session")).toBeInTheDocument();
        });

        it("defaults to dots variant", () => {
            const { container } = render(<LoadingSpinner />);
            // Dots variant has multiple bouncing elements
            const bounceElements = container.querySelectorAll(".animate-bounce");
            expect(bounceElements.length).toBeGreaterThan(0);
        });
    });

    describe("Variants", () => {
        it("renders dots variant", () => {
            const { container } = render(<LoadingSpinner variant="dots" />);
            const bounceElements = container.querySelectorAll(".animate-bounce");
            expect(bounceElements.length).toBe(3);
        });

        it("renders star variant", () => {
            const { container } = render(<LoadingSpinner variant="star" />);
            expect(container.querySelector("svg")).toBeInTheDocument();
        });

        it("renders pulse variant", () => {
            const { container } = render(<LoadingSpinner variant="pulse" />);
            // Pulse variant uses animate-ping for the ping effect
            expect(container.querySelector(".animate-ping")).toBeInTheDocument();
        });
    });

    describe("Sizes", () => {
        // Size classes are applied to the inner spinner element (first child of the wrapper)
        it("applies small size class", () => {
            const { container } = render(<LoadingSpinner size="sm" />);
            const innerSpinner = container.querySelector('[role="status"]')?.firstChild;
            expect(innerSpinner).toHaveClass("w-6", "h-6");
        });

        it("applies medium size class", () => {
            const { container } = render(<LoadingSpinner size="md" />);
            const innerSpinner = container.querySelector('[role="status"]')?.firstChild;
            expect(innerSpinner).toHaveClass("w-10", "h-10");
        });

        it("applies large size class", () => {
            const { container } = render(<LoadingSpinner size="lg" />);
            const innerSpinner = container.querySelector('[role="status"]')?.firstChild;
            expect(innerSpinner).toHaveClass("w-16", "h-16");
        });

        it("applies extra-large size class", () => {
            const { container } = render(<LoadingSpinner size="xl" />);
            const innerSpinner = container.querySelector('[role="status"]')?.firstChild;
            expect(innerSpinner).toHaveClass("w-24", "h-24");
        });
    });

    describe("Colors", () => {
        it("applies primary color class", () => {
            const { container } = render(<LoadingSpinner color="primary" />);
            const innerSpinner = container.querySelector('[role="status"]')?.firstChild;
            expect(innerSpinner).toHaveClass("text-primary");
        });

        it("applies white color for dark backgrounds", () => {
            const { container } = render(<LoadingSpinner color="white" />);
            const innerSpinner = container.querySelector('[role="status"]')?.firstChild;
            expect(innerSpinner).toHaveClass("text-white");
        });
    });

    describe("Accessibility", () => {
        it("has role status for screen readers", () => {
            render(<LoadingSpinner />);
            expect(screen.getByRole("status")).toBeInTheDocument();
        });

        it("is not focusable", () => {
            const { container } = render(<LoadingSpinner />);
            const spinner = container.firstChild as HTMLElement;
            expect(spinner).not.toHaveAttribute("tabindex");
        });
    });

    describe("Custom className", () => {
        it("applies additional custom classes", () => {
            const { container } = render(
                <LoadingSpinner className="my-custom-class" />
            );
            // Custom classes are passed to the inner spinner
            const innerSpinner = container.querySelector('[role="status"]')?.firstChild;
            expect(innerSpinner).toHaveClass("my-custom-class");
        });
    });
});
