import { setupServer } from 'msw/node'
import { repositoryHandlers } from './handlers/repository'
import { podcastHandlers } from './handlers/podcast'
import { chatHandlers } from './handlers/chat'

export const server = setupServer(...repositoryHandlers, ...podcastHandlers, ...chatHandlers)
