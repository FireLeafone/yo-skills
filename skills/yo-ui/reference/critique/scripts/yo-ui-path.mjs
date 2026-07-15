import path from 'node:path';

export const YO_UI_DIR = 'docs/yo-ui';
export const CRITIQUE_DIR = 'critique';

export function getYoUiDir(cwd = process.cwd()) {
  return path.join(cwd, YO_UI_DIR);
}

export function getCritiqueDir(cwd = process.cwd()) {
  return path.join(getYoUiDir(cwd), CRITIQUE_DIR);
}
