// Repository-related test fixtures

export const mockRepository = {
  repo_id: 'test1234',
  name: 'sample-project',
  description: 'A sample project for testing',
  file_count: 15,
}

export const mockFileTree = {
  repo_id: 'test1234',
  root: {
    name: 'sample-project',
    path: '.',
    is_dir: true,
    children: [
      {
        name: 'README.md',
        path: 'README.md',
        is_dir: false,
        children: null,
      },
      {
        name: 'pyproject.toml',
        path: 'pyproject.toml',
        is_dir: false,
        children: null,
      },
      {
        name: 'src',
        path: 'src',
        is_dir: true,
        children: [
          {
            name: '__init__.py',
            path: 'src/__init__.py',
            is_dir: false,
            children: null,
          },
          {
            name: 'main.py',
            path: 'src/main.py',
            is_dir: false,
            children: null,
          },
          {
            name: 'utils.py',
            path: 'src/utils.py',
            is_dir: false,
            children: null,
          },
          {
            name: 'models',
            path: 'src/models',
            is_dir: true,
            children: [
              {
                name: '__init__.py',
                path: 'src/models/__init__.py',
                is_dir: false,
                children: null,
              },
              {
                name: 'user.py',
                path: 'src/models/user.py',
                is_dir: false,
                children: null,
              },
            ],
          },
        ],
      },
      {
        name: 'tests',
        path: 'tests',
        is_dir: true,
        children: [
          {
            name: '__init__.py',
            path: 'tests/__init__.py',
            is_dir: false,
            children: null,
          },
          {
            name: 'test_main.py',
            path: 'tests/test_main.py',
            is_dir: false,
            children: null,
          },
        ],
      },
    ],
  },
}

export const validGitHubUrls = [
  'https://github.com/user/repo',
  'https://github.com/organization/project-name',
  'https://github.com/user/repo.git',
  'http://github.com/user/repo',
]

export const invalidGitHubUrls = [
  'not-a-url',
  'https://gitlab.com/user/repo',
  'github.com/user/repo', // missing protocol
  '',
]

export function createFileNode(overrides = {}) {
  return {
    name: 'test_file.py',
    path: 'test_file.py',
    is_dir: false,
    children: null,
    ...overrides,
  }
}

export function createDirectoryNode(name: string, children = []) {
  return {
    name,
    path: name,
    is_dir: true,
    children,
  }
}
