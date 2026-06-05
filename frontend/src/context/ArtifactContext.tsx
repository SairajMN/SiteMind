"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import { PageSummary, FormSummary, EndpointSummary, WorkflowSummary, CitationSchema } from "@/lib/api-client";

export type ArtifactType = "page" | "form" | "endpoint" | "workflow" | "citation";

export type SelectedArtifactUnion = 
  | { type: "page"; data: PageSummary }
  | { type: "form"; data: FormSummary }
  | { type: "endpoint"; data: EndpointSummary }
  | { type: "workflow"; data: WorkflowSummary }
  | { type: "citation"; data: CitationSchema }
  | null;

interface ArtifactContextType {
  selectedArtifact: SelectedArtifactUnion;
  panelOpen: boolean;
  setSelectedArtifact: (artifact: SelectedArtifactUnion) => void;
  closePanel: () => void;
  openPanel: () => void;
}

const ArtifactContext = createContext<ArtifactContextType | undefined>(undefined);

export function ArtifactProvider({ children }: { children: ReactNode }) {
  const [selectedArtifact, setSelectedArtifactState] = useState<SelectedArtifactUnion>(null);
  const [panelOpen, setPanelOpen] = useState(false);

  const setSelectedArtifact = (artifact: SelectedArtifactUnion) => {
    setSelectedArtifactState(artifact);
    if (artifact !== null) {
      setPanelOpen(true);
    }
  };

  const closePanel = () => {
    setPanelOpen(false);
  };

  const openPanel = () => {
    if (selectedArtifact) {
      setPanelOpen(true);
    }
  };

  return (
    <ArtifactContext.Provider
      value={{
        selectedArtifact,
        panelOpen,
        setSelectedArtifact,
        closePanel,
        openPanel,
      }}
    >
      {children}
    </ArtifactContext.Provider>
  );
}

export function useArtifact() {
  const context = useContext(ArtifactContext);
  if (!context) {
    throw new Error("useArtifact must be used within an ArtifactProvider");
  }
  return context;
}
