# TanStack Query Explained: From First Principles

## Table of Contents
1. [The Problem It Solves](#the-problem-it-solves)
2. [What Came Before](#what-came-before)
3. [What Is TanStack Query?](#what-is-tanstack-query)
4. [How It Works](#how-it-works)
5. [Real Example: Before & After](#real-example-before--after)
6. [Key Concepts](#key-concepts)
7. [When To Use It](#when-to-use-it)
8. [Configuration in This Project](#configuration-in-this-project)

---

## The Problem It Solves

### The Fundamental Challenge

In any web application, you need to do two types of data management:

1. **Client State** - Data that lives only in the browser
   - Form input values
   - UI state (is modal open?)
   - Selected tab

2. **Server State** - Data that lives on the server
   - User data
   - Product listings
   - API responses

**The problem:** Server state is fundamentally different from client state:
- You don't own it (the server does)
- It can become outdated
- Multiple users might modify it
- Network requests can fail
- Loading takes time

React's built-in state (`useState`) treats server data like client state, which creates problems.

---

## What Came Before

### Era 1: Manual Fetch with useState + useEffect (2018-2020)

This is what we had in the code **before** the refactoring.

```tsx
function ValuationsListPage() {
  // Manual state management
  const [valuations, setValuations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Manual fetching
  useEffect(() => {
    async function fetchValuations() {
      try {
        const data = await ValuationsAPI.list();
        setValuations(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchValuations();
  }, []);

  // Manual rendering logic
  if (loading) return <Spinner />;
  if (error) return <Error message={error} />;
  return <div>{/* render valuations */}</div>;
}
```

**Problems with this approach:**
1. **Boilerplate everywhere** - Every component needs 3 state variables + useEffect
2. **No caching** - Navigate away and back? Fetch again (slow, wasteful)
3. **No deduplication** - Multiple components fetch the same data? Multiple requests
4. **Stale data** - Data might be outdated, no way to know
5. **Race conditions** - Fast clicks can cause bugs
6. **No retry logic** - Network fails? User has to refresh
7. **No optimistic updates** - Can't show instant UI changes before server confirms

### Era 2: Redux + Thunks (2015-2020)

Some teams used Redux to manage server state:

```tsx
// Action creators
const fetchValuations = () => async (dispatch) => {
  dispatch({ type: 'FETCH_VALUATIONS_REQUEST' });
  try {
    const data = await api.list();
    dispatch({ type: 'FETCH_VALUATIONS_SUCCESS', payload: data });
  } catch (error) {
    dispatch({ type: 'FETCH_VALUATIONS_FAILURE', error });
  }
};

// Reducer
function valuationsReducer(state, action) {
  switch (action.type) {
    case 'FETCH_VALUATIONS_REQUEST':
      return { ...state, loading: true };
    case 'FETCH_VALUATIONS_SUCCESS':
      return { ...state, loading: false, data: action.payload };
    // ... more cases
  }
}
```

**Problems:**
1. **Even more boilerplate** - Actions, reducers, thunks
2. **Still no caching strategy** - You have to build it yourself
3. **Complex** - Steep learning curve
4. **Not designed for server state** - Redux was made for client state

---

## What Is TanStack Query?

### The Simple Answer

**TanStack Query is a library that handles server state for you.**

Instead of manually managing loading/error/data states, it gives you hooks that:
- Automatically handle loading states
- Automatically cache data
- Automatically refetch when needed
- Automatically dedupe requests
- Automatically handle errors

### The Philosophy

> "Treat server state differently from client state."

TanStack Query assumes:
- Server data is **asynchronous** (takes time to fetch)
- Server data is **shared** (multiple components might need it)
- Server data can become **stale** (outdated)
- Server data needs **synchronization** (keep in sync with server)

---

## How It Works

### Core Concept: Queries and Mutations

TanStack Query has two main concepts:

1. **Queries** - For reading data (GET requests)
   ```tsx
   const { data, isLoading, error } = useQuery({
     queryKey: ['valuations'],
     queryFn: () => ValuationsAPI.list()
   });
   ```

2. **Mutations** - For changing data (POST/PUT/DELETE requests)
   ```tsx
   const { mutate, isPending } = useMutation({
     mutationFn: (data) => ValuationsAPI.create(data)
   });
   ```

### The Query Key System

**Query keys** are how TanStack Query identifies and caches data:

```tsx
// Different keys = different cache entries
useQuery({ queryKey: ['valuations'] })           // All valuations
useQuery({ queryKey: ['valuations', '123'] })    // Specific valuation #123
useQuery({ queryKey: ['valuations', '456'] })    // Specific valuation #456
```

**Key benefits:**
1. **Automatic caching** - Same key = same cached data
2. **Smart invalidation** - Can invalidate by key pattern
3. **Deduplication** - Two components with same key = one request

### The Cache Lifecycle

```
1. Component mounts
   ↓
2. Check cache - Do we have data for this key?
   ├─ Yes → Return cached data (instant!)
   └─ No → Fetch from server
   ↓
3. Store in cache with key
   ↓
4. Component unmounts
   ↓
5. Keep cache alive for 5 minutes (configurable)
   ↓
6. After 5 minutes of no use → Garbage collect
```

### Background Refetching

Even when showing cached data, TanStack Query can refetch in the background:

```tsx
useQuery({
  queryKey: ['valuations'],
  queryFn: fetchValuations,
  staleTime: 5 * 60 * 1000, // Data is fresh for 5 minutes
  refetchOnWindowFocus: false // Don't refetch when user returns to tab
});
```

**Flow:**
1. User visits page → Fetch data → Show it
2. User navigates away
3. User returns within 5 minutes → Show cached data instantly
4. After 5 minutes → Fetch fresh data

---

## Real Example: Before & After

### Before TanStack Query (ValuationsListPage.tsx)

```tsx
function ValuationsListPage() {
  const navigate = useNavigate();

  // BOILERPLATE: Manual state management
  const [valuations, setValuations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // BOILERPLATE: Manual fetching logic
  useEffect(() => {
    async function fetchValuations() {
      try {
        const data = await ValuationsAPI.list();
        setValuations(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchValuations();
  }, []); // Have to remember dependency array

  // BOILERPLATE: Manual loading/error rendering
  if (loading) {
    return <div className="..."><Spinner /></div>;
  }

  if (error) {
    return <div className="...">Error: {error}</div>;
  }

  // Finally, the actual UI
  return (
    <div>
      {valuations.map(v => <ValuationCard key={v.id} {...v} />)}
    </div>
  );
}
```

**Line count:** ~30 lines of boilerplate before rendering anything

### After TanStack Query

```tsx
function ValuationsListPage() {
  const navigate = useNavigate();

  // ONE LINE: Get everything you need
  const { data: valuations = [], isLoading, error } = useValuations();

  // Render directly - TanStack Query handled the rest
  if (isLoading) return <Spinner />;
  if (error) return <Error message={error.message} />;

  return (
    <div>
      {valuations.map(v => <ValuationCard key={v.id} {...v} />)}
    </div>
  );
}
```

**Line count:** ~3 lines instead of 30

**Where did the logic go?** Into a reusable hook:

```tsx
// hooks/queries/useValuations.ts
export function useValuations() {
  return useQuery({
    queryKey: ['valuations'],
    queryFn: () => ValuationsAPI.list(),
  });
}
```

Now **every** component that needs valuations can just call `useValuations()` and:
- Get the same cached data (no duplicate requests)
- Share loading/error states
- Automatically stay in sync

---

## Key Concepts

### 1. Query Keys

Think of query keys as URLs for your cache:

```tsx
// Like: /valuations
useQuery({ queryKey: ['valuations'] })

// Like: /valuations/123
useQuery({ queryKey: ['valuations', '123'] })

// Like: /valuations?page=1&sort=date
useQuery({ queryKey: ['valuations', { page: 1, sort: 'date' }] })
```

### 2. Query Functions

The actual API call:

```tsx
useQuery({
  queryKey: ['valuations'],
  queryFn: async () => {
    const response = await fetch('/api/valuations');
    return response.json();
  }
});
```

### 3. Stale Time

How long data is considered "fresh":

```tsx
staleTime: 5 * 60 * 1000  // 5 minutes

// Within 5 minutes: Use cache, don't refetch
// After 5 minutes: Use cache, but refetch in background
```

### 4. Cache Time

How long to keep unused data in cache:

```tsx
cacheTime: 10 * 60 * 1000  // 10 minutes

// After component unmounts, keep data for 10 minutes
// If component remounts within 10 minutes, instant data
```

### 5. Automatic Refetching

TanStack Query refetches automatically:
- When window regains focus (can disable)
- When network reconnects
- At intervals (if configured)

### 6. Mutations with Cache Updates

When you change data, update the cache:

```tsx
const { mutate } = useMutation({
  mutationFn: (data) => ValuationsAPI.create(data),
  onSuccess: () => {
    // Invalidate the list to refetch fresh data
    queryClient.invalidateQueries({ queryKey: ['valuations'] });
  }
});
```

**Flow:**
1. User submits form
2. Mutation runs → Creates valuation on server
3. `onSuccess` fires → Invalidates `['valuations']` cache
4. Any component using `useValuations()` automatically refetches
5. UI updates everywhere with new data

---

## When To Use It

### ✅ Use TanStack Query When:

1. **Fetching data from APIs**
   - GET requests
   - Data that lives on a server

2. **Data shared across components**
   - Multiple components need the same data
   - Don't want to prop-drill or use context

3. **Need caching**
   - Avoid refetching on navigation
   - Speed up page transitions

4. **Need loading/error states**
   - Every API call needs loading spinner + error handling

5. **Production applications**
   - Need reliability, retries, error recovery

### ❌ Don't Use TanStack Query For:

1. **Pure client state**
   - Form input values → use `useState`
   - UI toggles (modals, dropdowns) → use `useState`
   - Derived state → use `useMemo`

2. **GraphQL with Apollo Client**
   - Apollo has its own caching (don't mix)

3. **Simple scripts/prototypes**
   - Overkill for one-off tools

---

## Configuration in This Project

### Setup (main.tsx)

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // Data fresh for 5 minutes
      refetchOnWindowFocus: false,    // Don't refetch on tab focus
      retry: 1,                       // Retry failed requests once
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <QueryClientProvider client={queryClient}>
    <App />
  </QueryClientProvider>
);
```

### Query Hooks (hooks/queries/)

**Pattern:** One hook per resource

```tsx
// hooks/queries/useValuations.ts
export function useValuations() {
  return useQuery({
    queryKey: ['valuations'],
    queryFn: () => ValuationsAPI.list(),
  });
}

// hooks/queries/useValuation.ts
export function useValuation(id: string) {
  return useQuery({
    queryKey: ['valuations', id],
    queryFn: () => ValuationsAPI.get(id),
    enabled: !!id, // Only fetch if ID exists
  });
}
```

### Mutation Hooks (hooks/mutations/)

**Pattern:** One hook per action

```tsx
// hooks/mutations/useRunAndSaveValuation.ts
export function useRunAndSaveValuation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data) => ValuationsAPI.runAndSave(data),
    onSuccess: () => {
      // Invalidate list to show new valuation
      queryClient.invalidateQueries({ queryKey: ['valuations'] });
    },
  });
}
```

---

## Benefits in This Project

### Before (Manual Approach)

**Per page:**
- 3 useState calls
- 1 useEffect
- Manual error handling
- Manual loading states
- ~15-20 lines of boilerplate

**Total:** ~60 lines across 3 pages

### After (TanStack Query)

**Per page:**
- 1 hook call
- Automatic error/loading handling
- ~1-3 lines

**Total:** ~10 lines across 3 pages + 25 lines of reusable hooks

**Net reduction:** ~40 lines + better DX + caching

---

## Common Patterns

### 1. Dependent Queries

Fetch data that depends on other data:

```tsx
const { data: user } = useUser(userId);
const { data: posts } = usePosts(user?.id, {
  enabled: !!user?.id  // Only fetch if user exists
});
```

### 2. Optimistic Updates

Update UI before server confirms:

```tsx
const { mutate } = useMutation({
  mutationFn: updateTodo,
  onMutate: async (newTodo) => {
    // Cancel refetch
    await queryClient.cancelQueries({ queryKey: ['todos'] });

    // Update cache optimistically
    queryClient.setQueryData(['todos'], (old) => [...old, newTodo]);

    // Return rollback value
    return { previousTodos };
  },
  onError: (err, newTodo, context) => {
    // Rollback on error
    queryClient.setQueryData(['todos'], context.previousTodos);
  }
});
```

### 3. Pagination

```tsx
const [page, setPage] = useState(1);

const { data } = useQuery({
  queryKey: ['valuations', page],
  queryFn: () => fetchValuations(page),
  keepPreviousData: true  // Don't flash loading on page change
});
```

---

## Resources

- **Official Docs:** https://tanstack.com/query/latest
- **Video Tutorial:** [React Query in 100 Seconds](https://www.youtube.com/watch?v=novnyCaa7To)
- **Comparison Article:** [React Query vs Redux](https://tkdodo.eu/blog/react-query-vs-redux)

---

## TL;DR

**What:** Library for managing server state in React

**Why:** Eliminates boilerplate, adds caching, handles errors/loading automatically

**Before:** 20 lines of useState/useEffect per page

**After:** 1 line per page, hooks handle the rest

**Trade-off:** Slight learning curve, but worth it for production apps

**In this project:** Reduced ~40 lines of boilerplate, added caching, better DX
