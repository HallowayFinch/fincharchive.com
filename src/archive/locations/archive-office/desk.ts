import { archiveOffice } from './location';
import { archiveMaterials } from '../../materials';

export const deskScene = {
  id: 'scene-0001',
  location: archiveOffice,
  name: archiveOffice.publicName,
  materials: [
    {
      ...archiveMaterials.caseFiles,
      x: 58,
      y: 38,
      width: 22,
      height: 24,
    },
    {
      ...archiveMaterials.fieldNotes,
      x: 18,
      y: 34,
      width: 18,
      height: 22,
    },
    {
      ...archiveMaterials.recorder,
      x: 45,
      y: 18,
      width: 18,
      height: 20,
    },
    {
      ...archiveMaterials.photographs,
      x: 38,
      y: 58,
      width: 20,
      height: 16,
    },
  ],
};
