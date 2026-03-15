import type { Destination } from "@/lib/destinations";

export type FavoriteItem = {
  id: string;
  name: string;
  location: string;
  image: string;
  shortDescription: string;
  savedAt: string;
};

const getFavoritesKey = (userId: number) => `trailmark-favorites-${userId}`;

export const getFavoriteItems = (userId: number): FavoriteItem[] => {
  try {
    const raw = localStorage.getItem(getFavoritesKey(userId));
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as FavoriteItem[];
  } catch {
    return [];
  }
};

export const isFavoriteDestination = (userId: number, destinationId: string) =>
  getFavoriteItems(userId).some((item) => item.id === destinationId);

export const toggleFavoriteDestination = (userId: number, destination: Destination) => {
  const current = getFavoriteItems(userId);
  const exists = current.some((item) => item.id === destination.id);
  const next: FavoriteItem[] = exists
    ? current.filter((item) => item.id !== destination.id)
    : [
        {
          id: destination.id,
          name: destination.name,
          location: destination.location,
          image: destination.image,
          shortDescription: destination.shortDescription,
          savedAt: new Date().toISOString(),
        },
        ...current,
      ];
  localStorage.setItem(getFavoritesKey(userId), JSON.stringify(next));
  return !exists;
};

export const removeFavoriteDestination = (userId: number, destinationId: string) => {
  const current = getFavoriteItems(userId);
  const next = current.filter((item) => item.id !== destinationId);
  localStorage.setItem(getFavoritesKey(userId), JSON.stringify(next));
  return next;
};

