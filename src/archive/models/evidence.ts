export type EvidenceType =
  | 'log'
  | 'field-note'
  | 'artifact'
  | 'transmission';

export type Evidence = {
  id: string;
  type: EvidenceType;
  title: string;
  date: string;
  permalink: string;
  related?: string[];
  tags?: string[];
  sceneObject?: string;
};
