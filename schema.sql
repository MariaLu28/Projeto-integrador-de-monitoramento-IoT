begin;

create table public.readings (
  device_id text not null check (device_id ~ '^[a-z0-9_-]{1,40}$'),
  message_id text not null check (length(trim(message_id)) between 1 and 120),
  luminosity double precision not null check (luminosity between 0 and 100000),
  received_at timestamptz not null default now(),
  primary key (device_id, message_id)
);

create index readings_device_time
on public.readings (device_id, received_at desc);

alter table public.readings enable row level security;

grant usage on schema public to anon, authenticated, service_role;

revoke all on public.readings from anon, authenticated;

grant select on public.readings to anon, authenticated;

grant all on public.readings to service_role;

create policy "synthetic_lab_public_read" on public.readings
  for select to anon, authenticated using (true);

commit;

-- Leitura pública apenas de dados sintéticos. Não há escrita pública.
