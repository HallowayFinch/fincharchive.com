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
      x: 5.99,
      y: 62.5,
      width: 24.74,
      height: 30.76,
    },
    {
      id: 'field-notes',
      label: 'Field Notebook',
      assetId: interactiveAssets['AO-103'].id,
      name: interactiveAssets['AO-103'].name,
      href: interactiveAssets['AO-103'].target,
      image: interactiveAssets['AO-103'].path,
      status: interactiveAssets['AO-103'].status,
      x: 32.23,
      y: 62.5,
      width: 19.53,
      height: 28.32,
    },
    {
      id: 'recorder',
      label: 'Recorder',
      assetId: interactiveAssets['AO-102'].id,
      name: interactiveAssets['AO-102'].name,
      href: interactiveAssets['AO-102'].target,
      image: interactiveAssets['AO-102'].path,
      status: interactiveAssets['AO-102'].status,
      x: 47.53,
      y: 48.83,
      width: 26.69,
      height: 26.37,
    },
    {
      id: 'photographs',
      label: 'Photographs',
      assetId: interactiveAssets['AO-104'].id,
      name: interactiveAssets['AO-104'].name,
      href: interactiveAssets['AO-104'].target,
      image: interactiveAssets['AO-104'].path,
      status: interactiveAssets['AO-104'].status,
      x: 73.89,
      y: 73.73,
      width: 24.74,
      height: 21.48,
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
      x: 63.48,
      y: 68.36,
      width: 14.97,
      height: 20.51,
    },
    {
      id: 'keys',
      label: 'Keys',
      assetId: ambientAssets['AO-106'].id,
      name: ambientAssets['AO-106'].name,
      image: ambientAssets['AO-106'].path,
      status: ambientAssets['AO-106'].status,
      x: 50.13,
      y: 75.68,
      width: 13.99,
      height: 16.6,
    },
    {
      id: 'desk-lamp',
      label: 'Desk Lamp',
      assetId: ambientAssets['AO-107'].id,
      name: ambientAssets['AO-107'].name,
      image: ambientAssets['AO-107'].path,
      status: ambientAssets['AO-107'].status,
      x: 74.54,
      y: 26.37,
      width: 25.46,
      height: 50.29,
    },
  ],
};
