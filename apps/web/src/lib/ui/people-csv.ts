// Bulk import of people (admin F31 to F34), with the running app's rules: the first line is a
// header, each later line is Name, Email, Password, Role split on commas and trimmed, and a line
// with any other shape or role is reported by its 1-based row number. Quoted fields are not
// supported, as on the running app.
import type { User } from '$lib/data';

export interface PersonRow {
  name: string;
  email: string;
  password: string;
  role: User['role'];
}

const ROLES = ['admin', 'user', 'pending'];

export const TEMPLATE = 'Name,Email,Password,Role\nJane Doe,jane@example.org,change-me,user\n';

export function readPeopleCsv(text: string): { people: PersonRow[]; problems: string[] } {
  const people: PersonRow[] = [];
  const problems: string[] = [];
  text
    .split('\n')
    .slice(1)
    .forEach((line, index) => {
      const row = index + 2;
      const cells = line.split(',').map((cell) => cell.trim());
      if (cells.length !== 4) {
        problems.push(`Row ${row}: expected Name, Email, Password, Role.`);
        return;
      }
      const [name, email, password, role] = cells;
      if (!ROLES.includes(role.toLowerCase())) {
        problems.push(`Row ${row}: the role must be admin, user or pending.`);
        return;
      }
      people.push({ name, email, password, role: role.toLowerCase() as User['role'] });
    });
  return { people, problems };
}
