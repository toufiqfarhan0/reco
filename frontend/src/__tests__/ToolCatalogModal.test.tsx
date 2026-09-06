import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ToolCatalogModal } from "@/components/ToolCatalogModal";
import { ToolSchema } from "@/lib/types";

const MOCK_TOOLS: ToolSchema[] = [
  {
    name: "parse_bank_statement",
    description: "Normalizes bank statement lines into transaction records.",
    parameters_schema: {
      type: "object",
      required: ["records"],
      properties: {
        records: { type: "array", description: "List of raw bank transaction rows" },
      },
    },
    deterministic: true,
    side_effect: false,
    risk_level: "LOW",
    category: "ingestion",
  },
  {
    name: "fuzzy_match_transactions",
    description: "Multi-factor similarity matcher aligning statement records.",
    parameters_schema: {
      type: "object",
      properties: {
        vendor_similarity_threshold: { type: "number", description: "Cosine similarity" },
      },
    },
    deterministic: false,
    side_effect: false,
    risk_level: "MEDIUM",
    category: "reconciliation",
  },
];

describe("ToolCatalogModal Component", () => {
  it("does not render when isOpen is false", () => {
    render(
      <ToolCatalogModal
        isOpen={false}
        onClose={vi.fn()}
        tools={MOCK_TOOLS}
        selectedTools={new Set(["parse_bank_statement"])}
        onToggleTool={vi.fn()}
      />
    );
    expect(screen.queryByText(/Central Tool Registry/i)).not.toBeInTheDocument();
  });

  it("renders tools and allows searching and toggling", () => {
    const onToggleTool = vi.fn();
    render(
      <ToolCatalogModal
        isOpen={true}
        onClose={vi.fn()}
        tools={MOCK_TOOLS}
        selectedTools={new Set(["parse_bank_statement"])}
        onToggleTool={onToggleTool}
      />
    );

    expect(screen.getByText(/Central Tool Registry/i)).toBeInTheDocument();
    expect(screen.getByText("parse_bank_statement")).toBeInTheDocument();
    expect(screen.getByText("fuzzy_match_transactions")).toBeInTheDocument();

    const searchInput = screen.getByPlaceholderText(/Search tools.../i);
    fireEvent.change(searchInput, { target: { value: "fuzzy" } });
    expect(screen.getByText("fuzzy_match_transactions")).toBeInTheDocument();
    expect(screen.queryByText("parse_bank_statement")).not.toBeInTheDocument();
  });
});
