import { Component, input } from '@angular/core';

@Component({
  selector: 'app-tag-list',
  standalone: true,
  templateUrl: './tag-list.component.html',
  styleUrl: './tag-list.component.scss',
})
export class TagListComponent {
  readonly tags = input.required<string[]>();
}
