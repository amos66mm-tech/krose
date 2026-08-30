import axios from 'axios'
import type {
  Activity,
  AgentStatus,
  CollectionRun,
  ContentIdeaCategory,
  Country,
  DashboardSummary,
  DocumentDetail,
  DocTypeOption,
  EntityDetail,
  EntityRef,
  GiftCardType,
  IntelOverview,
  Platform,
  PriceBoardCell,
  PriceQuote,
  SearchResponse,
  SocialPost,
  TagRef,
  WatchQuery,
} from '../types'

export const api = axios.create({ baseURL: '/api' })

export const fetchCountries = () => api.get<Country[]>('/countries').then((r) => r.data)

export const fetchPlatforms = (countryCode?: string) =>
  api.get<Platform[]>('/platforms', { params: { country_code: countryCode } }).then((r) => r.data)

export const fetchGiftCardTypes = () => api.get<GiftCardType[]>('/gift-card-types').then((r) => r.data)

export const fetchPriceBoard = (countryCode?: string) =>
  api.get<PriceBoardCell[]>('/prices/board', { params: { country_code: countryCode } }).then((r) => r.data)

export const fetchPriceHistory = (platformId: number, giftCardTypeId: number, days = 30) =>
  api
    .get<PriceQuote[]>('/prices/history', {
      params: { platform_id: platformId, gift_card_type_id: giftCardTypeId, days },
    })
    .then((r) => r.data)

export const fetchActivities = (countryCode?: string, limit = 50) =>
  api.get<Activity[]>('/activities', { params: { country_code: countryCode, limit } }).then((r) => r.data)

export const fetchSocialPosts = (countryCode?: string, limit = 50) =>
  api.get<SocialPost[]>('/social', { params: { country_code: countryCode, limit } }).then((r) => r.data)

export const fetchDashboardSummary = (countryCode?: string) =>
  api.get<DashboardSummary>('/dashboard/summary', { params: { country_code: countryCode } }).then((r) => r.data)

export const fetchIdeas = () => api.get<ContentIdeaCategory[]>('/ideas').then((r) => r.data)

export const fetchAgentStatus = () => api.get<AgentStatus>('/dashboard/agent-status').then((r) => r.data)

export const fetchRuns = (limit = 20) => api.get<CollectionRun[]>('/collect/runs', { params: { limit } }).then((r) => r.data)

export const triggerCollection = (scope = 'intel', countryCode?: string) =>
  api
    .post<CollectionRun[]>('/collect/run', null, { params: { scope, country_code: countryCode } })
    .then((r) => r.data)

export const fetchIntelOverview = (countryCode?: string) =>
  api.get<IntelOverview>('/intel/overview', { params: { country_code: countryCode } }).then((r) => r.data)

export const searchDocuments = (params: {
  q?: string
  countryCode?: string
  docType?: string
  stream?: string
  tag?: string
  entityId?: number
  sourceKind?: string
  limit?: number
}) =>
  api
    .get<SearchResponse>('/intel/search', {
      params: {
        q: params.q || undefined,
        country_code: params.countryCode,
        doc_type: params.docType,
        stream: params.stream,
        tag: params.tag,
        entity_id: params.entityId,
        source_kind: params.sourceKind,
        limit: params.limit ?? 40,
      },
    })
    .then((r) => r.data)

export const fetchDocument = (id: number) => api.get<DocumentDetail>(`/intel/documents/${id}`).then((r) => r.data)

export const fetchEntities = (params?: { entityType?: string; q?: string; discoveredOnly?: boolean }) =>
  api
    .get<EntityRef[]>('/intel/entities', {
      params: {
        entity_type: params?.entityType,
        q: params?.q,
        discovered_only: params?.discoveredOnly || undefined,
      },
    })
    .then((r) => r.data)

export const fetchEntity = (id: number) => api.get<EntityDetail>(`/intel/entities/${id}`).then((r) => r.data)

export const fetchTags = () => api.get<TagRef[]>('/intel/tags').then((r) => r.data)

export const fetchDocTypes = () => api.get<DocTypeOption[]>('/intel/doc-types').then((r) => r.data)

export const fetchWatches = () => api.get<WatchQuery[]>('/watches').then((r) => r.data)

export const createWatch = (query: string, label: string, countryCode?: string) =>
  api.post<WatchQuery>('/watches', { query, label, country_code: countryCode, save: true }).then((r) => r.data)

export const patchWatch = (id: number, isActive: boolean) =>
  api.patch<WatchQuery>(`/watches/${id}`, { is_active: isActive }).then((r) => r.data)

export const deleteWatch = (id: number) => api.delete(`/watches/${id}`).then((r) => r.data)

export const runWatch = (id: number) => api.post(`/watches/${id}/run`).then((r) => r.data)

export const runCustomCollect = (query: string, label: string, countryCode?: string) =>
  api.post('/collect/custom', { query, label, country_code: countryCode, save: true, run_now: true }).then((r) => r.data)
