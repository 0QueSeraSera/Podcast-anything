import { setupServer } from 'msw/node'
import { repositoryHandlers } from './handlers/repository'
import { podcastHandlers } from './handlers/podcast'

export const server = setupServer(...repositoryHandlers, ...podcastHandlers)
