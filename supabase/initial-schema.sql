-- Esquema inicial aplicado al proyecto nuevo, sin datos del proyecto anterior.
create table public.entries (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null default auth.uid() references auth.users(id) on delete cascade,
 kind text not null check (kind in ('trip','plan','place','goal','preferences')),
 title text not null check (char_length(title) between 1 and 180),
 data jsonb not null default '{}'::jsonb check (jsonb_typeof(data) = 'object'),
 deleted_at timestamptz,
 updated_at timestamptz not null default now(),
 revision integer not null default 1
);
create index entries_user_kind_idx on public.entries(user_id,kind);
alter table public.entries enable row level security;
create policy entries_select on public.entries for select to authenticated using ((select auth.uid()) = user_id);
create policy entries_insert on public.entries for insert to authenticated with check ((select auth.uid()) = user_id);
create policy entries_update on public.entries for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy entries_delete on public.entries for delete to authenticated using ((select auth.uid()) = user_id);
revoke all on public.entries from anon;
grant select,insert,update,delete on public.entries to authenticated;
create function public.update_entry_revision() returns trigger language plpgsql security invoker set search_path = '' as $$ begin new.updated_at = now(); new.revision = old.revision + 1; return new; end $$;
create trigger entries_revision before update on public.entries for each row execute function public.update_entry_revision();
insert into storage.buckets (id,name,public,file_size_limit,allowed_mime_types) values ('photos','photos',false,10485760,array['image/jpeg','image/png','image/webp']);
create policy private_photos_select on storage.objects for select to authenticated using (bucket_id='photos' and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy private_photos_insert on storage.objects for insert to authenticated with check (bucket_id='photos' and (storage.foldername(name))[1]=(select auth.uid())::text);
create policy private_photos_delete on storage.objects for delete to authenticated using (bucket_id='photos' and (storage.foldername(name))[1]=(select auth.uid())::text);
