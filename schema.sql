create extension if not exists "uuid-ossp";

create table products (
    id              uuid primary key default uuid_generate_v4(),
    name            text not null,
    brand           text,
    category        text,
    image_url       text,
    created_at      timestamptz default now()
);

create table listings (
    id              uuid primary key default uuid_generate_v4(),
    product_id      uuid references products(id) on delete cascade,  -- nullable until matched
    platform        text not null check (platform in ('kilimall', 'jumia')),
    platform_sku    text,
    url             text not null,
    title_raw       text,
    current_price   numeric(10,2),
    currency        text default 'KES',
    is_active       boolean default true,
    match_status    text default 'pending' check (match_status in ('pending', 'matched', 'no_match_needs_review')),
    last_checked_at timestamptz,
    created_at      timestamptz default now(),
    unique(platform, url)
);

create index idx_listings_product on listings(product_id);
create index idx_listings_match_status on listings(match_status);

create table price_history (
    id              bigserial primary key,
    listing_id      uuid references listings(id) on delete cascade,
    price           numeric(10,2) not null,
    recorded_at     timestamptz default now()
);

create index idx_price_history_listing_time on price_history(listing_id, recorded_at desc);

create table alerts (
    id                  uuid primary key default uuid_generate_v4(),
    user_id             uuid references auth.users(id) on delete cascade,
    product_id          uuid references products(id) on delete cascade,
    listing_id          uuid references listings(id) on delete cascade,  -- null = "any platform"
    alert_type          text check (alert_type in ('target_price', 'percent_drop', 'any_drop')),
    target_price        numeric(10,2),
    percent_threshold   numeric(5,2),
    is_active           boolean default true,
    last_triggered_at   timestamptz,
    created_at          timestamptz default now()
);
create index idx_alerts_user on alerts(user_id);
create index idx_alerts_product on alerts(product_id);

create table notifications_sent (
    id          uuid primary key default uuid_generate_v4(),
    alert_id    uuid references alerts(id) on delete cascade,
    channel     text check (channel in ('email', 'sms', 'push')),
    sent_at     timestamptz default now(),
    old_price   numeric(10,2),
    new_price   numeric(10,2)
);
