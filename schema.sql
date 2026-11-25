
begin;

create table public.readings (
  device_id text not null
    check (device_id ~ '^[a-z0-9_-]{1,40}$'),

  message_id text not null
    check (length(trim(message_id)) between 1 and 120),

  sensor_id text,

  luminosity double precision not null,

  received_at timestamptz not null default now(),

  primary key (device_id, message_id),

  constraint readings_sensor_id_check
    check (
      sensor_id is null or
      sensor_id in (
        'batata',
        'soja',
        'amendoim'
      )
    ),

  constraint readings_luminosity_check
    check (
      luminosity >= 0 and
      luminosity <= 100000
    )
);

-- Índice para consultar leituras por dispositivo e horário
create index readings_device_time
on public.readings (device_id, received_at desc);

-- Segurança e permissões
alter table public.readings enable row level security;

grant usage on schema public to anon, authenticated, service_role;

revoke all on public.readings from anon, authenticated;

grant select on public.readings to anon, authenticated;

grant all on public.readings to service_role;

-- Permitir consulta pública das leituras
create policy "synthetic_lab_public_read" on public.readings
  for select to anon, authenticated using (true);

commit;
