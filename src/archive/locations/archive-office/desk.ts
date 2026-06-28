import { archiveOffice } from './location';
import { archiveOfficeAssets } from '../../assets/archive-office';
import type { LocationSceneData } from '../../models/scene';

const interactiveAssets = Object.fromEntries(
  archiveOfficeAssets.interactive.map((asset) => [asset.id, asset]),
);

export const deskScene: LocationSceneData = {
  id: 'scene-0001',
  location: archiveOffice,
  name: archiveOffice.publicName,
  materials: [
    {
      id: 'case-files',
      label: 'Case Folder',
      assetId: interactiveAssets['AO-101'].id,
      name: interactiveAssets['AO-101'].name,
      href: interactiveAssets['AO-101'].target,
      image: interactiveAssets['AO-101'].path,
      status: interactiveAssets['AO-101'].status,
      x: 11,
      y: 66,
      width: 22,
      height: 20,
    },
    {
      id: 'field-notes',
      label: 'Field Notebook',
      assetId: interactiveAssets['AO-103'].id,
      name: interactiveAssets['AO-103'].name,
      href: interactiveAssets['AO-103'].target,
      image: interactiveAssets['AO-103'].path,
      status: interactiveAssets['AO-103'].status,
      x: 35,
      y: 64,
      width: 17,
      height: 19,
    },
    {
      id: 'recorder',
      label: 'Recorder',
      assetId: interactiveAssets['AO-102'].id,
      name: interactiveAssets['AO-102'].name,
      href: interactiveAssets['AO-102'].target,
      image: interactiveAssets['AO-102'].path,
      status: interactiveAssets['AO-102'].status,
      x: 52,
      y: 43,
      width: 22,
      height: 24,
    },
    {
      id: 'photographs',
      label: 'Photographs',
      assetId: interactiveAssets['AO-104'].id,
      name: interactiveAssets['AO-104'].name,
      href: interactiveAssets['AO-104'].target,
      image: interactiveAssets['AO-104'].path,
      status: interactiveAssets['AO-104'].status,
      x: 77,
      y: 67,
      width: 17,
      height: 15,
    },
  ],
};
