export interface Country {
  id: number
  code: string
  name_zh: string
  name_en: string
  currency_code: string
  flag_emoji: string
}

export interface Platform {
  id: number
  country_id: number
  slug: string
  name: string
  website: string
  category: string
  logo_url: string
  twitter_handle: string
  facebook_handle: string
  instagram_handle: string
  telegram_handle: string
  trust_score: number
  notes: string
}

export interface GiftCardType {
  id: number
  slug: string
  name: string
  icon: string
}

export interface PriceBoardCell {
  platform_id: number
  platform_name: string
  gift_card_type_id: number
  gift_card_type_name: string
  gift_card_icon: string
  rate_percent: number
  currency: string
  is_new: boolean
  change_percent: number
  collected_at: string
  source_url: string
}

export interface PriceQuote {
  id: number
  platform_id: number
  gift_card_type_id: number
  direction: string
  rate_percent: number
  price_value: number
  currency: string
  unit_description: string
  source_url: string
  source_title: string
  is_new: boolean
  change_percent: number
  collected_at: string
}

export interface Activity {
  id: number
  platform_id: number
  activity_type: string
  title: string
  summary: string
  source_url: string
  published_at: string | null
  collected_at: string
}

export interface SocialPost {
  id: number
  platform_id: number
  network: string
  author: string
  content: string
  url: string
  sentiment: string
  engagement_score: number
  published_at: string | null
  collected_at: string
}

export interface DashboardSummary {
  total_countries: number
  total_platforms: number
  total_price_points_24h: number
  new_price_points_24h: number
  active_promotions_7d: number
  social_posts_7d: number
  live_mode: boolean
  last_run: CollectionRun | null
  best_rate_per_card_type: {
    gift_card_type: string
    icon: string
    platform: string
    rate_percent: number
    currency: string
  }[]
  biggest_movers: {
    platform: string
    gift_card_type: string
    change_percent: number
    rate_percent: number
    currency: string
  }[]
}

export interface ContentIdeaItem {
  title: string
  description: string
  priority: string
}

export interface ContentIdeaCategory {
  category: string
  items: ContentIdeaItem[]
}

export interface CollectionRun {
  id: number
  scope: string
  mode: 'live' | 'mock' | 'demo'
  status: 'running' | 'success' | 'failed'
  targets_processed: number
  records_created: number
  error_message: string
  started_at: string
  finished_at: string | null
}

export interface AgentStatus {
  has_exa: boolean
  has_llm: boolean
  live_mode: boolean
  can_collect: boolean
  llm_model: string
  llm_base_url: string
  collection_interval_minutes: number
  scheduler_enabled: boolean
  search_results_per_watch: number
  document_count: number
  watch_count: number
}

export interface EntityRef {
  id: number
  name: string
  entity_type: string
  slug: string
  mention_count: number
  is_seeded: boolean
  country_code?: string | null
}

export interface TagRef {
  id: number
  slug: string
  name: string
  category: string
  document_count: number
}

export interface DocumentListItem {
  id: number
  title: string
  url: string
  snippet: string
  summary_zh: string
  source_domain: string
  source_kind: string
  stream: string
  country_code: string | null
  doc_type: string
  sentiment: string
  is_demo: boolean
  is_analyzed: boolean
  relevance: number
  collected_at: string
  published_at: string | null
  entities: EntityRef[]
  tags: TagRef[]
}

export interface Fact {
  claim: string
  kind: string
  value?: string | null
}

export interface DocumentDetail extends DocumentListItem {
  full_text: string
  author: string
  query: string
  hit_count: number
  facts: Fact[]
  related: DocumentListItem[]
}

export interface EntityDetail extends EntityRef {
  description: string
  aliases: string[]
  first_seen_at: string
  last_seen_at: string
  platform_id: number | null
  documents: DocumentListItem[]
  related_entities: EntityRef[]
}

export interface CountRow {
  key: string
  label: string
  count: number
}

export interface IntelOverview {
  total_documents: number
  documents_24h: number
  total_entities: number
  discovered_entities: number
  unanalyzed: number
  watch_count: number
  live_mode: boolean
  last_run: CollectionRun | null
  doc_type_counts: CountRow[]
  tag_counts: CountRow[]
  stream_counts: CountRow[]
  top_entities: EntityRef[]
  emerging_entities: EntityRef[]
  top_domains: CountRow[]
}

export interface SearchResponse {
  query: string
  total: number
  items: DocumentListItem[]
}

export interface WatchQuery {
  id: number
  key: string
  label: string
  query: string
  stream: string
  country_code: string | null
  include_domains: string
  exa_category: string
  is_active: boolean
  is_system: boolean
  notes: string
  created_at: string
}

export interface DocTypeOption {
  key: string
  label: string
}
