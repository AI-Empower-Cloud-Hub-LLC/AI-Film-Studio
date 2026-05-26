import ProjectDetail from './ProjectDetail'

export async function generateStaticParams() {
  return []
}

export const dynamicParams = false

export default function ProjectPage() {
  return <ProjectDetail />
}
