export type SceneObject = {
  id: string;
  label: string;
  assetId?: string;
  name?: string;
  status?: string;
  href: string;
  image?: string;
  x: number;
  y: number;
  width: number;
  height: number;
};

export type LocationSceneData = {
  id: string;
  name: string;
  location: {
    assets: {
      background: string;
    };
  };
  materials: SceneObject[];
};
