import { archiveOffice } from './location';
import { archiveOfficeAssets } from '../../assets/archive-office';
import type { LocationSceneData } from '../../models/scene';

const interactiveAssets = Object.fromEntries(
  archiveOfficeAssets.interactive.map((asset) => [asset.id, asset]),
);

const ambientAssets = Object.fromEntries(
  archiveOfficeAssets.ambient.map((asset) => [asset.id, asset]),
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
      x: 5.2,
      y: 64.6,
      width: 18.6,
      height: 22.2,
    },
    {
      id: 'field-notes',
      label: 'Field Notebook',
      assetId: interactiveAssets['AO-103'].id,
      name: interactiveAssets['AO-103'].name,
      href: interactiveAssets['AO-103'].target,
      image: interactiveAssets['AO-103'].path,
      status: interactiveAssets['AO-103'].status,
      x: 25.4,
      y: 64.4,
      width: 11.8,
      height: 20,
    },
    {
      id: 'recorder',
      label: 'Recorder',
      assetId: interactiveAssets['AO-102'].id,
      name: interactiveAssets['AO-102'].name,
      href: interactiveAssets['AO-102'].target,
      image: interactiveAssets['AO-102'].path,
      status: interactiveAssets['AO-102'].status,
      x: 39.4,
      y: 52.7,
      width: 25.2,
      height: 26.2,
    },
    {
      id: 'photographs',
      label: 'Photographs',
      assetId: interactiveAssets['AO-104'].id,
      name: interactiveAssets['AO-104'].name,
      href: interactiveAssets['AO-104'].target,
      image: interactiveAssets['AO-104'].path,
      status: interactiveAssets['AO-104'].status,
      x: 80.4,
      y: 64.1,
      width: 13.5,
      height: 15.9,
    },
  ],
  ambient: [
    {
      id: 'mug',
      label: 'Coffee Mug',
      assetId: ambientAssets['AO-105'].id,
      name: ambientAssets['AO-105'].name,
      image: ambientAssets['AO-105'].path,
      status: ambientAssets['AO-105'].status,
      x: 67.6,
      y: 61.9,
      width: 11.2,
      height: 17.4,
    },
    {
      id: 'keys',
      label: 'Keys',
      assetId: ambientAssets['AO-106'].id,
      name: ambientAssets['AO-106'].name,
      image: ambientAssets['AO-106'].path,
      status: ambientAssets['AO-106'].status,
      x: 44.9,
      y: 76.7,
      width: 12.4,
      height: 9.4,
    },
  ],
};
