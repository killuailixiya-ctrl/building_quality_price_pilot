create table images (
  id uuid primary key default gen_random_uuid(),
  pic_id text not null,
  url text not null,
  created_at timestamptz default now()
);

create table comparison_results (
  id uuid primary key default gen_random_uuid(),
  annotator_id text not null,
  left_id uuid not null references images(id),
  right_id uuid not null references images(id),
  result text not null check (result in ('left','right','equal')),
  created_at timestamptz default now()
);

create index comparison_results_annotator_idx on comparison_results(annotator_id);
