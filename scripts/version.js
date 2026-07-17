const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

/**
 * Bump a semver version string.
 * @param {string} current - Current version (e.g. "0.1.0")
 * @param {string} releaseType - "patch", "minor", "major", or explicit version
 * @returns {string} New version string
 */
function bumpVersion(current, releaseType) {
  // If releaseType looks like a semver version, return it directly
  if (/^\d+\.\d+\.\d+$/.test(releaseType)) {
    return releaseType;
  }

  const parts = current.split('.').map(Number);
  if (parts.length !== 3 || parts.some(isNaN)) {
    throw new Error(`Invalid current version: ${current}`);
  }

  const [major, minor, patch] = parts;

  switch (releaseType) {
    case 'patch':
      return `${major}.${minor}.${patch + 1}`;
    case 'minor':
      return `${major}.${minor + 1}.0`;
    case 'major':
      return `${major + 1}.0.0`;
    default:
      throw new Error(`Invalid release type: ${releaseType}. Expected patch, minor, major, or explicit version.`);
  }
}

/**
 * Update the version field in multiple JSON files.
 * Rolls back all files if any update fails.
 * @param {string} newVersion - The new version to set
 * @param {string[]} filePaths - Array of JSON file paths
 */
function updateVersionInFiles(newVersion, filePaths) {
  const originals = [];

  try {
    for (const filePath of filePaths) {
      const content = fs.readFileSync(filePath, 'utf8');
      originals.push({ filePath, content });

      const obj = JSON.parse(content);
      obj.version = newVersion;

      // Marketplace manifests also carry a version per plugin entry
      if (Array.isArray(obj.plugins)) {
        for (const plugin of obj.plugins) {
          if (plugin && typeof plugin === 'object' && 'version' in plugin) {
            plugin.version = newVersion;
          }
        }
      }

      fs.writeFileSync(filePath, JSON.stringify(obj, null, 2) + '\n');
    }
  } catch (err) {
    // Rollback all already-modified files
    for (const { filePath, content } of originals) {
      try {
        fs.writeFileSync(filePath, content);
      } catch (rollbackErr) {
        // Ignore rollback errors
      }
    }
    throw new Error(`Failed to update version in files: ${err.message}`);
  }
}

/**
 * Generate or append to a CHANGELOG.md file.
 * @param {string} version - Version string
 * @param {string} date - Date string
 * @param {string[]} commits - Array of commit subject lines
 * @param {string} changelogPath - Path to CHANGELOG.md
 */
function generateChangelog(version, date, commits, changelogPath) {
  const versionSection = `## ${version} (${date})\n\n${commits.map(c => `- ${c}`).join('\n')}\n`;

  if (!fs.existsSync(changelogPath)) {
    const content = `# Changelog\n\n${versionSection}`;
    fs.writeFileSync(changelogPath, content);
    return;
  }

  const existingContent = fs.readFileSync(changelogPath, 'utf8');

  // Insert after the # Changelog header, normalizing extra blank lines
  const headerMatch = existingContent.match(/^# Changelog\s*\n/);
  if (headerMatch) {
    const rest = existingContent.slice(headerMatch[0].length).replace(/^\n+/, '');
    const newContent = `# Changelog\n\n${versionSection}${rest}`;
    fs.writeFileSync(changelogPath, newContent);
  } else {
    // No header found, prepend
    fs.writeFileSync(changelogPath, `# Changelog\n\n${versionSection}\n${existingContent}`);
  }
}

const RELEASE_COMMIT_PATTERN = /\brelease\s+\d+\.\d+\.\d+\b/i;

/**
 * Check whether a commit subject is a version release commit.
 * @param {string} subject - Commit subject line
 * @returns {boolean}
 */
function isReleaseCommit(subject) {
  return RELEASE_COMMIT_PATTERN.test(subject);
}

/**
 * Find the most recent release commit hash (e.g. "chore: release 0.2.0").
 * @returns {string|null} Commit hash, or null if none found
 */
function getLastReleaseCommitHash() {
  try {
    const output = execSync('git log "--pretty=format:%H|%s"', {
      encoding: 'utf8',
      stdio: 'pipe'
    }).trim();

    if (!output) {
      return null;
    }

    for (const line of output.split('\n')) {
      const pipeIndex = line.indexOf('|');
      if (pipeIndex === -1) {
        continue;
      }

      const hash = line.slice(0, pipeIndex);
      const subject = line.slice(pipeIndex + 1);
      if (isReleaseCommit(subject)) {
        return hash;
      }
    }

    return null;
  } catch (err) {
    return null;
  }
}

/**
 * Get git commit subjects since the last release point.
 * Priority: last git tag → last release commit → all commits (first release).
 * Release commits themselves are excluded from the result.
 * @returns {string[]} Array of commit subject lines
 */
function getCommitsSinceLastTag() {
  try {
    const tagList = execSync('git tag -l', { encoding: 'utf8', stdio: 'pipe' }).trim();
    const hasTags = tagList.length > 0;

    let rangeStart;
    if (hasTags) {
      rangeStart = execSync('git describe --tags --abbrev=0', {
        encoding: 'utf8',
        stdio: 'pipe'
      }).trim();
    } else {
      rangeStart = getLastReleaseCommitHash();
    }

    const logCmd = rangeStart
      ? `git log ${rangeStart}..HEAD --pretty=format:%s`
      : 'git log --pretty=format:%s';

    const output = execSync(logCmd, { encoding: 'utf8', stdio: 'pipe' }).trim();

    if (!output) {
      return [];
    }

    return output
      .split('\n')
      .filter(subject => !isReleaseCommit(subject));
  } catch (err) {
    return [];
  }
}

// ── CLI entry point ──────────────────────────────────────────────────────────

if (require.main === module) {
  const releaseType = process.argv[2];

  if (!releaseType) {
    console.error('Usage: node scripts/version.js <patch|minor|major|version>');
    process.exit(1);
  }

  try {
    const packagePath = path.join(process.cwd(), 'package.json');
    const packageJson = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    const currentVersion = packageJson.version;

    console.log(`Current version: ${currentVersion}`);

    const newVersion = bumpVersion(currentVersion, releaseType);
    console.log(`New version: ${newVersion}`);

    const filesToUpdate = [
      path.join(process.cwd(), 'package.json'),
      path.join(process.cwd(), '.claude-plugin', 'plugin.json'),
      path.join(process.cwd(), '.claude-plugin', 'marketplace.json'),
      path.join(process.cwd(), '.codex-plugin', 'plugin.json'),
      path.join(process.cwd(), '.kimi-plugin', 'plugin.json')
    ];

    console.log('Updating version in JSON files...');
    updateVersionInFiles(newVersion, filesToUpdate);
    console.log('  done');

    const today = new Date().toISOString().split('T')[0];
    const commits = getCommitsSinceLastTag();
    const changelogPath = path.join(process.cwd(), 'CHANGELOG.md');

    console.log(`Generating CHANGELOG.md with ${commits.length} commit(s)...`);
    generateChangelog(newVersion, today, commits, changelogPath);
    console.log('  done');

    console.log(`\nVersion bumped to ${newVersion}`);
  } catch (err) {
    console.error(`Error: ${err.message}`);
    process.exit(1);
  }
}

module.exports = {
  bumpVersion,
  updateVersionInFiles,
  generateChangelog,
  isReleaseCommit,
  getLastReleaseCommitHash,
  getCommitsSinceLastTag
};
