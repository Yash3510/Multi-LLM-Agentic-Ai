import { describe, expect, it } from 'vitest';
import { readPeopleCsv, TEMPLATE } from './people-csv';

describe('people CSV import (admin F33)', () => {
  it('skips the header, keeps 4-column rows with a known role, and names bad rows', () => {
    const text = [
      'Name,Email,Password,Role',
      'Ravi Kumar, ravi@plant.test ,demo-only-5,User',
      'Bad Row,bad@plant.test,demo-only-6',
      'Meera,meera@plant.test,demo-only-7,owner',
      '',
    ].join('\n');
    const { people, problems } = readPeopleCsv(text);
    expect(people).toEqual([
      { name: 'Ravi Kumar', email: 'ravi@plant.test', password: 'demo-only-5', role: 'user' },
    ]);
    expect(problems).toEqual([
      'Row 3: expected Name, Email, Password, Role.',
      'Row 4: the role must be admin, user or pending.',
      'Row 5: expected Name, Email, Password, Role.',
    ]);
  });

  it('offers a template with the four columns', () => {
    expect(TEMPLATE.split('\n')[0]).toBe('Name,Email,Password,Role');
  });
});
