-- Create Profiles Table (Linked to Auth)
create table public.profiles (
  id uuid references auth.users not null primary key,
  email text,
  icr_breakfast float default 10.0,
  icr_lunch float default 15.0,
  icr_dinner float default 20.0,
  icr_snack float default 15.0,
  isf float default 50.0,
  target_glucose integer default 90,
  correction_threshold integer default 120,
  weight float default 70.0,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for Profiles
alter table public.profiles enable row level security;

create policy "Users can view own profile" on public.profiles
  for select using (auth.uid() = id);

create policy "Users can update own profile" on public.profiles
  for update using (auth.uid() = id);

create policy "Users can insert own profile" on public.profiles
  for insert with check (auth.uid() = id);


-- Create Logs Table
create table public.logs (
  id uuid default gen_random_uuid() primary key,
  user_id uuid references auth.users not null,
  timestamp timestamp with time zone default timezone('utc'::text, now()) not null,
  glucose integer not null,
  carbs integer not null,
  activity text,
  emotion text,
  recommended_dose float,
  actual_dose float,
  notes text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Enable RLS for Logs
alter table public.logs enable row level security;

create policy "Users can view own logs" on public.logs
  for select using (auth.uid() = user_id);

create policy "Users can insert own logs" on public.logs
  for insert with check (auth.uid() = user_id);

create policy "Users can delete own logs" on public.logs
  for delete using (auth.uid() = user_id);

-- Trigger to create profile on signup
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email);
  return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
