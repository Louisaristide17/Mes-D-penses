import {
  Briefcase,
  Bus,
  Car,
  CircleEllipsis,
  Gift,
  GraduationCap,
  HeartPulse,
  House,
  PiggyBank,
  Plane,
  Receipt,
  Shirt,
  Smartphone,
  Tag,
  Ticket,
  Users,
  Utensils,
} from 'lucide-react'

// Les noms sont ceux stockés par l'API dans le champ "icon" des catégories.
export const CATEGORY_ICONS = {
  utensils: Utensils,
  bus: Bus,
  home: House,
  receipt: Receipt,
  smartphone: Smartphone,
  'heart-pulse': HeartPulse,
  'graduation-cap': GraduationCap,
  ticket: Ticket,
  shirt: Shirt,
  'circle-ellipsis': CircleEllipsis,
  users: Users,
  gift: Gift,
  'piggy-bank': PiggyBank,
  briefcase: Briefcase,
  car: Car,
  plane: Plane,
  tag: Tag,
}

export const CUSTOM_ICONS = ['tag', 'users', 'gift', 'piggy-bank', 'briefcase', 'car', 'plane']
export const CUSTOM_COLORS = ['#0F5D4A', '#2F6FB0', '#7A5AA6', '#B7791F', '#1E8A8A', '#B4483A', '#C0567F']

export function CategoryIcon({ category, size = 28 }) {
  const Icon = CATEGORY_ICONS[category.icon] || Tag
  return (
    <span
      className="category-dot"
      style={{ width: size, height: size, background: `${category.color}1F`, color: category.color }}
      aria-hidden="true"
    >
      <Icon size={Math.round(size * 0.55)} strokeWidth={1.75} />
    </span>
  )
}

export function CategoryLabel({ category }) {
  return (
    <span className="category">
      <CategoryIcon category={category} />
      {category.name}
    </span>
  )
}
