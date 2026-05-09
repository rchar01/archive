import MiniSearch, { type SearchOptions, type SearchResult } from 'minisearch'

const TAG_QUERY_RE = /#[\p{L}\p{N}]+(?:-[\p{L}\p{N}]+)*\*?/u

type ResultFilter = NonNullable<SearchOptions['filter']>
type SearchFunction = MiniSearch['search']

function isPageLevelResult(result: SearchResult): boolean {
  // VitePress 1.6.x stores section hits as `/page#heading` and page hits as
  // `/page`; the synthetic tag records intentionally use the page form.
  return typeof result.id === 'string' && !result.id.includes('#')
}

function combineFilters(...filters: ResultFilter[]): ResultFilter {
  return (result) => filters.every((filter) => filter(result))
}

export function patchLocalSearch(): void {
  const prototype = MiniSearch.prototype as MiniSearch & { __archiveLocalSearchPatched?: boolean }
  if (prototype.__archiveLocalSearchPatched) {
    return
  }

  const search = prototype.search as SearchFunction
  prototype.search = function patchedSearch(query, searchOptions = {}) {
    if (typeof query !== 'string') {
      return search.call(this, query, searchOptions)
    }

    const filter = searchOptions.filter
    if (TAG_QUERY_RE.test(query)) {
      return search.call(this, query, {
        ...searchOptions,
        combineWith: 'AND',
        filter: filter ? combineFilters(filter, isPageLevelResult) : isPageLevelResult,
      })
    }

    return search.call(this, query, {
      ...searchOptions,
      filter: filter
        ? combineFilters(filter, (result) => !isPageLevelResult(result))
        : (result) => !isPageLevelResult(result),
    })
  } as SearchFunction
  prototype.__archiveLocalSearchPatched = true
}
